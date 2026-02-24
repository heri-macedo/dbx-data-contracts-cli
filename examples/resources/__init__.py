"""
Bundle resources loader - Entry point for DAB Python support.

This is the ONLY file needed in the client's resources/ folder.
All job generation logic is in the databricks-contracts library.

Reference: https://docs.databricks.com/aws/en/dev-tools/bundles/python/
"""

from databricks.bundles.core import Bundle, Resources

from databricks_contracts.adapters.databricks import ContractJobGenerator


def load_resources(bundle: Bundle) -> Resources:
    """
    Load resources function referenced in databricks.yaml.

    Creates Databricks jobs dynamically based on contract files.

    The contracts path is resolved automatically.
    The wheel path is resolved from ${var.CONTRACTS_WHEEL_PATH}.

    Args:
        bundle: Bundle context with variables and target info.

    Returns:
        Resources containing all generated jobs.
    """
    generator = ContractJobGenerator(bundle)
    return generator.create_resources()
