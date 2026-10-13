import sys
import types

# The engine imports SentenceTransformer at module load. Tests stub the model,
# so register a lightweight fake when the real package (and torch) is absent.
if "sentence_transformers" not in sys.modules:
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        fake = types.ModuleType("sentence_transformers")
        fake.SentenceTransformer = object
        sys.modules["sentence_transformers"] = fake
