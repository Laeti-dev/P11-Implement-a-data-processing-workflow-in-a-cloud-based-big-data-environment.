# Apprentissage techniques du projet

Ce document regroupe les points techniques importants appris au fil du projet, afin de garder une trace exploitable pour de futurs travaux (maintenance, extension de l’architecture, nouveaux projets Big Data, etc.).

---

## PySpark et contraintes techniques

### Travailler dans un environnement Java / Spark

- **Dépendance forte à la JVM**
  PySpark repose sur Apache Spark, lui‑même basé sur la JVM (Java Virtual Machine). Même si le code applicatif est écrit en Python, l’exécution distribuée se fait via des processus Java.
  - Nécessité d’avoir une version de Java compatible avec la version de Spark utilisée.
  - Variables d’environnement à soigner (`JAVA_HOME`, `SPARK_HOME`, configuration du `PATH`, etc.).
  - Sur des environnements managés (EMR, Docker, etc.), il est préférable de laisser l’image ou le service gérer la version de Java plutôt que d’installer Java localement.

- **Couplage avec la version de Spark**
  - La version de PySpark doit être alignée avec celle de Spark déployée sur le cluster (ou dans l’image Docker).
  - Un décalage de version peut provoquer des erreurs difficiles à diagnostiquer (problèmes de sérialisation, incompatibilités de jars, options de configuration manquantes).

### Contraintes d’exécution distribuée

- **Sérialisation des objets Python**
  - Le code Python est converti en tâches exécutées côté JVM ; les objets doivent donc être sérialisables.
  - Éviter d’embarquer des objets complexes ou non sérialisables dans les fonctions passées à `map`, `foreach`, `udf`, etc.
  - Préférer les UDF simples et, lorsque c’est possible, utiliser les fonctions natives de Spark SQL / DataFrame plutôt que des UDF Python, plus coûteuses.

- **Gestion des ressources (mémoire, CPU)**
  - La répartition mémoire entre le driver et les executors est critique : une mauvaise configuration peut conduire à des `OutOfMemoryError` côté JVM.
  - Les paramètres tels que `spark.executor.memory`, `spark.driver.memory`, `spark.executor.cores` doivent être ajustés en fonction de la taille des données et des ressources disponibles (cluster EMR, environnement Docker, etc.).
  - Penser à la persistance et au cache (`persist`, `cache`) avec parcimonie pour ne pas saturer la mémoire.

### Intégration avec d’autres bibliothèques (TensorFlow, etc.)

- **Passerelles entre monde distribué et monde local**
  - Les modèles TensorFlow/Keras sont généralement chargés en mémoire sur le driver, puis utilisés dans des UDF ou des fonctions de transformation.
  - Il peut être nécessaire de **diffuser** (broadcast) certains objets (poids de modèle, dictionnaires, paramètres) pour éviter de les recopier à chaque tâche.

- **Coût des allers‑retours**
  - Les conversions DataFrame ⇔ Pandas ou DataFrame ⇔ RDD peuvent être très coûteuses. Il faut limiter ces passages au strict nécessaire.
  - Les phases lourdes de calcul (inférence de modèle, PCA, etc.) doivent idéalement rester dans l’environnement Spark pour bénéficier du parallélisme.

### Gestion de l’environnement (local, Docker, EMR)

- **Reproductibilité de l’environnement**
  - L’utilisation de Docker permet de figer la combinaison Java + Spark + PySpark + dépendances Python, ce qui réduit les différences entre machine locale et cluster.
  - Sur EMR, la configuration se fait surtout via les options du cluster et d’éventuels scripts bootstrap ; il faut documenter précisément ces choix (type de nœuds, version d’EMR, version de Spark, options d’instance).

- **Gestion des variables d’environnement et des secrets**
  - Les chemins S3, les clés d’API (ex. Kaggle), et autres secrets ne doivent pas être codés en dur dans le code PySpark.
  - Utiliser des fichiers `.env`, des systèmes de gestion de secrets (AWS Secrets Manager, Parameter Store), ou des variables d’environnement injectées au runtime.

### Broadcasting des poids de modèle

- **Objectif du broadcasting**
  Le but est de partager un objet « lourd » (par exemple les poids d’un modèle TensorFlow/Keras ou un grand dictionnaire) avec tous les executors **sans le recopier intégralement pour chaque tâche**.
  - Le driver envoie une seule copie de l’objet aux nœuds du cluster.
  - Les tâches accèdent ensuite à cet objet via une référence locale, ce qui réduit drastiquement les transferts réseau et le temps de sérialisation.

- **Principe d’utilisation avec PySpark**
  - Le modèle (ou ses poids) est initialisé sur le driver.
  - On crée une variable broadcast avec `sc.broadcast(objet)`.
  - Dans les UDF ou les fonctions de transformation, on lit l’objet via `broadcast.value`.
  - On évite ainsi de recharger le modèle à chaque appel de l’UDF ou pour chaque partition.

- **Bonnes pratiques**
  - **Taille raisonnable** : seules les structures de taille modérée doivent être broadcastées. Un modèle gigantesque peut dépasser la mémoire disponible sur les executors.
  - **Immutabilité logique** : l’objet broadcasté ne doit pas être modifié dans les tâches ; on le considère comme en lecture seule.
  - **Nettoyage** : lorsque l’objet n’est plus nécessaire (enchaînement de jobs très différents), penser à libérer la variable broadcast (`unpersist` / recréer une nouvelle variable si besoin).

- **Limites et points d’attention**
  - Le broadcasting ne résout pas tous les problèmes de performance : si l’inférence du modèle est très coûteuse, il faut également optimiser la logique métier (batching, réduction de la taille des features, etc.).
  - En environnement EMR ou Docker, il est crucial que la **même version du framework de deep learning** (TensorFlow, PyTorch, etc.) soit disponible sur tous les nœuds, sinon le chargement des poids ou l’exécution du code peut échouer.
  - Lors de l’évolution du modèle (nouveaux poids, nouvelle architecture), penser à versionner et documenter quelle version est utilisée dans quel job Spark.

- **Cas concret du projet (`MobileNetV2`)**
  - Le modèle est chargé une fois côté driver, puis ses poids sont récupérés avec `get_weights()`.
  - Ces poids sont diffusés avec une variable broadcast pour éviter de recharger le modèle depuis le stockage sur chaque tâche.
  - Dans la `pandas_udf`, chaque executor reconstruit un modèle local (`weights=None`) puis applique les poids broadcastés (`set_weights(...)`).
  - Cette approche réduit l’I/O redondante, diminue le coût de démarrage des tasks et garantit une inférence cohérente entre partitions.

### Extraction de features et scalabilité

- **Définition opérationnelle**
  - L’extraction de features consiste à transformer chaque image brute en un vecteur numérique (embedding) via un modèle pré-entraîné utilisé comme extracteur (`include_top=False`, `pooling='avg'`).
  - Dans le projet, on passe d’images (bytes) à une colonne `features` exploitable dans Spark ML.

- **Objectif métier et technique**
  - Découpler la phase deep learning (coûteuse) des étapes ML aval (classification, clustering, analyse).
  - Réutiliser les features calculées une seule fois, plutôt que de refaire l’inférence à chaque expérimentation.
  - Préparer une réduction de dimension (PCA) pour alléger les traitements suivants.

- **Pourquoi c’est scalable avec Spark**
  - Les images sont distribuées en partitions ; chaque executor traite ses lots en parallèle via `pandas_udf`.
  - Le modèle est initialisé une fois par worker (mode `SCALAR_ITER`) au lieu d’être recréé pour chaque ligne.
  - Le broadcast des poids évite la duplication coûteuse des chargements.
  - Le filtrage des erreurs (`features IS NOT NULL`) permet de rendre le pipeline plus robuste aux images corrompues.

- **Optimisations de pipeline à retenir**
  - **Partitionnement** : ajuster `repartition(...)` selon le volume de données et le nombre d’executors.
  - **Cache** : conserver en mémoire les features quand elles sont réutilisées dans plusieurs actions Spark.
  - **Persistance** : écrire en Parquet pour reprendre facilement le travail entre sessions/job runs.
  - **Réduction de dimension** : appliquer PCA pour passer d’un embedding dense à une représentation plus compacte, réduisant coût mémoire et temps d’apprentissage.

- **Points de vigilance**
  - Le débit réel dépend surtout du ratio CPU/GPU disponible, de la taille des batches, et de la bande passante I/O.
  - Une sur-partition peut créer beaucoup d’overhead de scheduling ; une sous-partition peut sous-utiliser le cluster.
  - Le schéma des features (taille, type, version de modèle) doit être versionné pour garantir la reproductibilité.
---
