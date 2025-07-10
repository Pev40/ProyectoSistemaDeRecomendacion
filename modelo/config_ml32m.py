from config import GSASRecExperimentConfig

config = GSASRecExperimentConfig(
    dataset_name='ml32m',
    sequence_length=200,
    embedding_dim=256,        # Aumentado de 128 a 512
    num_heads=8,             # Aumentado de 2 a 8 # Modified to be divisible by embedding_dim
    max_batches_per_epoch=512,
    num_blocks=4,            # Aumentado de 2 a 4
    dropout_rate=0.2,        # Reducido de 0.3 a 0.2
    negs_per_pos=16,
    gbce_t=0.75,
    # Configuración optimizada para RTX 3050 6GB
    train_batch_size=128,    # Reducido para más parámetros
    max_epochs=500,          # Reducido de 3000
    early_stopping_patience=50,  # Más agresivo
    eval_batch_size=128,
)
