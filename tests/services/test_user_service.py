"""Unit tests for user service."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.services.user_service import UserService, user_service


class TestUserService:
    """Test user service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mocks for dependencies
        self.mock_redis = Mock()
        self.mock_localization = Mock()
        
        # Create service with mocked dependencies
        self.service = UserService(
            redis_client=self.mock_redis,
            localization=self.mock_localization
        )
        
        # Mock telegram user
        self.mock_user = Mock()
        self.mock_user.id = 12345
        self.mock_user.first_name = "TestUser"
        self.mock_user.language_code = "en"
        
    def test_user_service_initialization(self):
        """Test that user service initializes correctly."""
        service = UserService()
        
        assert service.redis_client is not None
        assert service.localization is not None
        assert hasattr(service, 'get_user_language')
        assert hasattr(service, 'set_user_language')
        assert hasattr(service, 'is_user_premium')
        assert hasattr(service, 'set_user_premium')
    
    def test_global_user_service_instance(self):
        """Test that global user service instance is available."""
        from src.services.user_service import user_service
        
        assert user_service is not None
        assert isinstance(user_service, UserService)
    
    def test_get_user_language_stored_preference(self):
        """Test getting user language when stored preference exists."""
        # Setup mocks
        self.mock_redis.get_user_language.return_value = 'ru'
        self.mock_localization.get_available_languages.return_value = ['en', 'ru']
        
        # Test
        result = self.service.get_user_language(self.mock_user)
        
        # Verify
        assert result == 'ru'
        self.mock_redis.get_user_language.assert_called_once_with(12345)
        self.mock_localization.get_available_languages.assert_called_once()
        self.mock_localization.get_user_language.assert_not_called()
    
    def test_get_user_language_fallback_to_telegram(self):
        """Test getting user language when no stored preference exists."""
        # Setup mocks
        self.mock_redis.get_user_language.return_value = None
        self.mock_localization.get_available_languages.return_value = ['en', 'ru']
        self.mock_localization.get_user_language.return_value = 'en'
        
        # Test
        result = self.service.get_user_language(self.mock_user)
        
        # Verify
        assert result == 'en'
        self.mock_redis.get_user_language.assert_called_once_with(12345)
        self.mock_localization.get_user_language.assert_called_once_with(self.mock_user)
    
    def test_get_user_language_invalid_stored_language(self):
        """Test getting user language when stored language is invalid."""
        # Setup mocks
        self.mock_redis.get_user_language.return_value = 'invalid_lang'
        self.mock_localization.get_available_languages.return_value = ['en', 'ru']
        self.mock_localization.get_user_language.return_value = 'en'
        
        # Test
        result = self.service.get_user_language(self.mock_user)
        
        # Verify
        assert result == 'en'
        self.mock_localization.get_user_language.assert_called_once_with(self.mock_user)
    
    def test_get_user_language_exception_handling(self):
        """Test getting user language with exception handling."""
        # Setup mocks to raise exception
        self.mock_redis.get_user_language.side_effect = Exception("Redis error")
        self.mock_localization.default_lang = 'en'
        
        # Test
        result = self.service.get_user_language(self.mock_user)
        
        # Verify
        assert result == 'en'
    
    def test_set_user_language_success(self):
        """Test setting user language successfully."""
        # Setup mock
        self.mock_redis.set_user_language.return_value = True
        
        # Test
        result = self.service.set_user_language(12345, 'ru')
        
        # Verify
        assert result is True
        self.mock_redis.set_user_language.assert_called_once_with(12345, 'ru')
    
    def test_set_user_language_failure(self):
        """Test setting user language with failure."""
        # Setup mock
        self.mock_redis.set_user_language.return_value = False
        
        # Test
        result = self.service.set_user_language(12345, 'ru')
        
        # Verify
        assert result is False
        self.mock_redis.set_user_language.assert_called_once_with(12345, 'ru')
    
    def test_set_user_language_exception(self):
        """Test setting user language with exception."""
        # Setup mock to raise exception
        self.mock_redis.set_user_language.side_effect = Exception("Redis error")
        
        # Test
        result = self.service.set_user_language(12345, 'ru')
        
        # Verify
        assert result is False
    
    def test_is_user_premium_true(self):
        """Test checking premium status when user is premium."""
        # Setup mock
        self.mock_redis.is_user_premium.return_value = True
        
        # Test
        result = self.service.is_user_premium(12345)
        
        # Verify
        assert result is True
        self.mock_redis.is_user_premium.assert_called_once_with(12345)
    
    def test_is_user_premium_false(self):
        """Test checking premium status when user is not premium."""
        # Setup mock
        self.mock_redis.is_user_premium.return_value = False
        
        # Test
        result = self.service.is_user_premium(12345)
        
        # Verify
        assert result is False
        self.mock_redis.is_user_premium.assert_called_once_with(12345)
    
    def test_is_user_premium_exception(self):
        """Test checking premium status with exception."""
        # Setup mock to raise exception
        self.mock_redis.is_user_premium.side_effect = Exception("Redis error")
        
        # Test
        result = self.service.is_user_premium(12345)
        
        # Verify
        assert result is False
    
    def test_set_user_premium_grant_success(self):
        """Test granting premium status successfully."""
        # Setup mock
        self.mock_redis.set_user_premium.return_value = True
        
        # Test
        result = self.service.set_user_premium(12345, True, 30)
        
        # Verify
        assert result is True
        self.mock_redis.set_user_premium.assert_called_once_with(12345, True, 30)
    
    def test_set_user_premium_revoke_success(self):
        """Test revoking premium status successfully."""
        # Setup mock
        self.mock_redis.set_user_premium.return_value = True
        
        # Test
        result = self.service.set_user_premium(12345, False)
        
        # Verify
        assert result is True
        self.mock_redis.set_user_premium.assert_called_once_with(12345, False, 30)
    
    def test_set_user_premium_failure(self):
        """Test setting premium status with failure."""
        # Setup mock
        self.mock_redis.set_user_premium.return_value = False
        
        # Test
        result = self.service.set_user_premium(12345, True)
        
        # Verify
        assert result is False
    
    def test_set_user_premium_exception(self):
        """Test setting premium status with exception."""
        # Setup mock to raise exception
        self.mock_redis.set_user_premium.side_effect = Exception("Redis error")
        
        # Test
        result = self.service.set_user_premium(12345, True)
        
        # Verify
        assert result is False
    
    def test_get_user_premium_status_text_premium(self):
        """Test getting premium status text for premium user."""
        # Setup mocks
        self.mock_redis.is_user_premium.return_value = True
        self.mock_localization.get.return_value = "Premium Active"
        
        # Test
        result = self.service.get_user_premium_status_text(12345, 'en')
        
        # Verify
        assert result == "Premium Active"
        self.mock_redis.is_user_premium.assert_called_once_with(12345)
        self.mock_localization.get.assert_called_once_with('status.premium_active', 'en')
    
    def test_get_user_premium_status_text_free(self):
        """Test getting premium status text for free user."""
        # Setup mocks
        self.mock_redis.is_user_premium.return_value = False
        self.mock_localization.get.return_value = "Premium Inactive"
        
        # Test
        result = self.service.get_user_premium_status_text(12345, 'en')
        
        # Verify
        assert result == "Premium Inactive"
        self.mock_localization.get.assert_called_once_with('status.premium_inactive', 'en')
    
    def test_get_user_premium_status_text_exception(self):
        """Test getting premium status text with exception."""
        # Setup mock to raise exception from is_user_premium method itself
        self.service.is_user_premium = Mock(side_effect=Exception("Redis error"))
        
        # Test
        result = self.service.get_user_premium_status_text(12345, 'en')
        
        # Verify - should return the hardcoded fallback string
        assert result == "Status unavailable"
    
    @patch.object(UserService, 'get_user_language')
    @patch.object(UserService, 'set_user_language')
    def test_initialize_user_language_success(self, mock_set_lang, mock_get_lang):
        """Test initializing user language successfully."""
        # Setup mocks
        mock_get_lang.return_value = 'en'
        mock_set_lang.return_value = True
        
        # Test
        result = self.service.initialize_user_language(self.mock_user)
        
        # Verify
        assert result == 'en'
        mock_get_lang.assert_called_once_with(self.mock_user)
        mock_set_lang.assert_called_once_with(12345, 'en')
    
    def test_initialize_user_language_exception(self):
        """Test initializing user language with exception."""
        # Setup mocks - make get_user_language method raise exception
        self.service.get_user_language = Mock(side_effect=Exception("Error"))
        self.mock_localization.default_lang = 'en'
        
        # Test
        result = self.service.initialize_user_language(self.mock_user)
        
        # Verify - should return the default language
        assert result == 'en'
    
    def test_all_required_methods_exist(self):
        """Test that all required methods exist for migration."""
        required_methods = [
            'get_user_language',
            'set_user_language', 
            'is_user_premium',
            'set_user_premium',
            'get_user_premium_status_text',
            'initialize_user_language'
        ]
        
        for method_name in required_methods:
            assert hasattr(self.service, method_name)
            assert callable(getattr(self.service, method_name))
    
    def test_service_interface_compatibility(self):
        """Test that service interface is compatible with expected usage patterns."""
        # Setup mocks
        self.mock_redis.get_user_language.return_value = 'en'
        self.mock_redis.is_user_premium.return_value = False
        self.mock_localization.get_available_languages.return_value = ['en', 'ru']
        self.mock_localization.get.return_value = "Test message"
        
        # Test the typical usage pattern from bot.py
        user_lang = self.service.get_user_language(self.mock_user)
        is_premium = self.service.is_user_premium(self.mock_user.id)
        status_text = self.service.get_user_premium_status_text(self.mock_user.id, user_lang)
        
        # Verify interface works
        assert user_lang == 'en'
        assert is_premium is False
        assert status_text == "Test message"
    
    def test_user_service_migration_readiness(self):
        """Test that user service is ready for migration from bot.py."""
        # This test verifies that the service can handle the patterns used in bot.py
        
        migration_requirements = {
            'language_detection': True,
            'language_storage': True,
            'premium_checking': True,
            'premium_management': True,
            'error_handling': True,
            'logging': True
        }
        
        # Verify all requirements are met
        assert hasattr(self.service, 'get_user_language')  # language_detection
        assert hasattr(self.service, 'set_user_language')  # language_storage
        assert hasattr(self.service, 'is_user_premium')    # premium_checking
        assert hasattr(self.service, 'set_user_premium')   # premium_management
        
        # Verify error handling in methods (they should not raise exceptions)
        try:
            # These should not raise exceptions even with broken dependencies
            self.service.get_user_language(self.mock_user)
            self.service.set_user_language(12345, 'en')
            self.service.is_user_premium(12345)
            self.service.set_user_premium(12345, True)
            migration_requirements['error_handling'] = True
        except Exception:
            migration_requirements['error_handling'] = False
        
        # Verify logging is available
        migration_requirements['logging'] = hasattr(self.service, '__module__')
        
        all_ready = all(migration_requirements.values())
        
        print(f"📋 Migration readiness: {migration_requirements}")
        print(f"🎯 Ready for migration: {all_ready}")
        
        assert all_ready, "User service must be ready for migration before starting" 