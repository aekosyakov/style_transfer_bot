"""
Billing and pricing configuration for the Style Transfer Bot.
All prices, quotas, and billing-related settings are centralized here.
"""

# Stars billing configuration
BILLING_CONFIG = {
    # Pass configurations
    "passes": {
        "pro_1day": {
            "price_stars": 3,
            "flux_quota": 5,
            "kling_quota": 2,
            "duration_hours": 1,
            "margin_percent": 61.8,
            "name_key": "billing.pass.pro_1day"
        },
        "creator_7day": {
            "price_stars": 5,
            "flux_quota": 10,
            "kling_quota": 3,
            "duration_hours": 12,
            "margin_percent": 42.5,
            "name_key": "billing.pass.creator_7day"
        },
        "studio_30day": {
            "price_stars": 10,
            "flux_quota": 15,
            "kling_quota": 5,
            "duration_hours": 24,
            "margin_percent": 31.1,
            "name_key": "billing.pass.studio_30day"
        }
    },
    
    # Pay-as-you-go configurations
    "payg": {
        "flux_extra": {
            "price_stars": 1,
            "quota": 1,
            "margin_percent": 88,
            "name_key": "billing.payg.flux_extra"
        },
        "kling_extra": {
            "price_stars": 2,
            "quota": 1,
            "margin_percent": 92,
            "name_key": "billing.payg.kling_extra"
        }
    },
    
    # Free user quotas
    "free_quotas": {
        "flux_daily": 5,      # 5 free FLUX generations per day
        "kling_daily": 1,     # 1 free Kling animation per day
        "expiration_hours": 24  # Daily reset
    },
    
    # Quota warning thresholds
    "warnings": {
        "gentle_warning_threshold": 3,  # Show gentle warning when ≤3 credits
        "hard_block_threshold": 0       # Show hard block when ≤0 credits
    },
    
    # Redis TTL settings (in seconds)
    "redis_ttl": {
        "interrupted_processing": 3600,    # 1 hour
        "auto_resume_context": 300,        # 5 minutes
        "auto_resume_flag": 300            # 5 minutes
    }
}

# Production pricing (commented out, ready to activate)
PRODUCTION_BILLING_CONFIG = {
    "passes": {
        "pro_1day": {
            "price_stars": 499,
            "flux_quota": 50,
            "kling_quota": 10,
            "duration_hours": 24,
            "margin_percent": 61.8,
            "name_key": "billing.pass.pro_1day"
        },
        "creator_7day": {
            "price_stars": 2999,
            "flux_quota": 500,
            "kling_quota": 50,
            "duration_hours": 24 * 7,
            "margin_percent": 42.5,
            "name_key": "billing.pass.creator_7day"
        },
        "studio_30day": {
            "price_stars": 9999,
            "flux_quota": 2000,
            "kling_quota": 200,
            "duration_hours": 24 * 30,
            "margin_percent": 31.1,
            "name_key": "billing.pass.studio_30day"
        }
    },
    
    "payg": {
        "flux_extra": {
            "price_stars": 25,
            "quota": 1,
            "margin_percent": 88,
            "name_key": "billing.payg.flux_extra"
        },
        "kling_extra": {
            "price_stars": 50,
            "quota": 1,
            "margin_percent": 92,
            "name_key": "billing.payg.kling_extra"
        }
    }
}


def get_billing_config():
    """Get the current billing configuration."""
    return BILLING_CONFIG


def get_pass_config(pass_id: str):
    """Get configuration for a specific pass."""
    return BILLING_CONFIG["passes"].get(pass_id)


def get_payg_config(payg_id: str):
    """Get configuration for a specific pay-as-you-go item."""
    return BILLING_CONFIG["payg"].get(payg_id)


def get_pass_price(pass_id: str):
    """Get the price for a specific pass."""
    config = get_pass_config(pass_id)
    return config["price_stars"] if config else 0


def get_payg_price(payg_id: str):
    """Get the price for a specific pay-as-you-go item."""
    config = get_payg_config(payg_id)
    return config["price_stars"] if config else 0 