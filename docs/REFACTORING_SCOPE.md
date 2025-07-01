# Bot.py Refactoring Scope Mapping

## 📊 **Current Analysis**
- **Total lines**: 1803
- **Target**: Files under 300 lines each  
- **Public methods**: 22/20 (too many)
- **Pylint score**: 1.56/10 (needs improvement)

## 🎯 **Extraction Plan**

### ✅ **COMPLETED: utils/logging_utils.py (97 lines)**
- `setup_logging()` - line 46
- `generate_request_id()` - line 68  
- `log_user_action()` - line 112
- `log_api_call()` - line 123
- `log_processing_step()` - line 140
- **Status**: ✅ Extracted, tested, committed

### 🔄 **NEXT: utils/retry_utils.py (~80 lines)**
- `retry_telegram_request()` - line 72
- **Dependencies**: asyncio, telegram imports, logging
- **Risk**: Low - standalone async utility

### 📝 **utils/validation.py (~100 lines)**
- Extract file validation logic from `handle_photo()` and `handle_document()`
- File size checks, MIME type validation
- **Dependencies**: None (pure validation logic)

### 🎨 **ui/keyboards.py (~150 lines)**
- `_get_main_menu_keyboard()` - line 817
- `_get_enhancement_keyboard()` - line 833
- **Dependencies**: localization, redis_client (for premium status)

### 🎨 **ui/menus.py (~200 lines)**
- `_show_main_menu()` - line 851
- `_show_premium_options()` - line 861
- `_show_enhancement_menu()` - line 890
- `_show_upload_prompt()` - line 901
- `_show_help_message()` - line 909
- **Dependencies**: keyboards.py, localization

### 👤 **services/user_service.py (~150 lines)**
- `_get_user_language()` - line 227
- User premium status management
- Language preference handling
- **Dependencies**: redis_client, localization

### 🔧 **services/processing_service.py (~200 lines)**
- Category logic: `_is_hairstyle_category()`, `_is_dress_category()`
- Gender mapping: `_get_hairstyle_category_from_original()`, `_get_dress_category_from_original()`
- Variation creation: `_create_varied_option()`
- **Dependencies**: prompt_variations

### 📊 **services/analytics_service.py (~100 lines)**
- User action tracking (extracted from command handlers)
- Processing step monitoring  
- Usage statistics
- **Dependencies**: logging_utils

### 🎮 **handlers/command_handlers.py (~400 lines)**
- All `/command` methods: start, premium, status, settings, feedback, about, invite, support, quota, buy, style, video, help
- Debug commands: debug_premium, debug_revoke
- **Dependencies**: services, ui

### 📩 **handlers/message_handlers.py (~200 lines)**
- `handle_photo()` - line 618
- `handle_document()` - line 655  
- `handle_text()` - line 707
- **Dependencies**: validation, processing_service

### 🔄 **handlers/callback_handlers.py (~300 lines)**
- `handle_callback_query()` - line 719
- `_handle_category_selection()` - line 931
- `_handle_option_selection()` - line 1003
- All button handlers: retry, restart, animate, etc.
- **Dependencies**: services, ui

### 💰 **handlers/payment_handlers.py (~150 lines)**
- `handle_pre_checkout_query()` - line 801
- `handle_successful_payment()` - line 807
- Auto-resume logic
- **Dependencies**: stars_billing

### 🏗️ **FINAL: src/bot.py (~150 lines)**
- `main()` function
- `StyleTransferBot.__init__()`
- `_setup_handlers()` - handler registration only
- Dependency injection coordination
- Application lifecycle

## 📈 **Progress Tracking**
- ✅ **Phase 1**: utils/logging_utils.py (DONE)
- 🔄 **Phase 2**: Complete utils package  
- ⏳ **Phase 3**: Extract services
- ⏳ **Phase 4**: Extract UI components
- ⏳ **Phase 5**: Extract handlers
- ⏳ **Phase 6**: Refactor main bot class

## 🎯 **Success Metrics**
- All files under 300 lines ✅ (logging_utils: 97 lines)
- Pylint score > 8.0 (currently 1.56)
- All tests pass ✅
- No circular dependencies 
- Clear single responsibilities ✅ 