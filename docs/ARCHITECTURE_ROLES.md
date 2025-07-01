# Bot Architecture Roles Definition

## 🏗️ **Component Definitions**

### **1. Utils (`utils/`)**
**Purpose**: Standalone helper functions with no business logic dependencies
**Scope**: 
- `logging_utils.py` - Logging setup, request ID generation, structured logging functions
- `retry_utils.py` - Telegram API retry logic, network error handling 
- `validation.py` - Input validation, file size/type checks

**Rules**:
- ✅ Can import: Standard library, telegram types
- ❌ Cannot import: Other bot modules, business logic
- 📏 Max complexity: Simple pure functions

### **2. Services (`services/`)**
**Purpose**: Business logic and state management 
**Scope**:
- `user_service.py` - User language, premium status, preferences
- `processing_service.py` - Image/video processing coordination, category logic
- `analytics_service.py` - User action tracking, metrics

**Rules**:
- ✅ Can import: Utils, external services (redis, config)
- ❌ Cannot import: Handlers, UI components
- 📏 Max complexity: Focused business operations

### **3. UI (`ui/`)**
**Purpose**: User interface components and presentation logic
**Scope**:
- `keyboards.py` - InlineKeyboardMarkup generators, button creation
- `menus.py` - Menu navigation, category displays  
- `messages.py` - Message formatting, text templates

**Rules**:
- ✅ Can import: Services, localization
- ❌ Cannot import: Handlers, telegram update objects directly
- 📏 Max complexity: Pure presentation logic

### **4. Handlers (`handlers/`)**
**Purpose**: Request/response handling and workflow coordination
**Scope**:
- `command_handlers.py` - All /command implementations
- `message_handlers.py` - Photo, document, text message processing
- `callback_handlers.py` - Button press and callback query handling
- `payment_handlers.py` - Payment processing and billing workflows

**Rules**:
- ✅ Can import: Services, UI, utils
- ✅ Can access: Telegram Update and Context objects
- ❌ Cannot import: Other handlers directly
- 📏 Max complexity: Workflow orchestration only

### **5. Main Bot (`src/bot.py`)**
**Purpose**: Application entry point and dependency coordination
**Scope**:
- Dependency injection container
- Handler registration
- Application lifecycle management

**Rules**:
- ✅ Can import: All modules for injection
- 📏 Target: ~150 lines, coordination only

## 🎯 **Migration Order** 
Following Gemini's "pilot first" approach:

1. **Pilot**: Extract `utils/logging_utils.py` (lowest risk, no dependencies)
2. **Utils**: Complete utils extraction
3. **Services**: Extract business logic 
4. **UI**: Extract presentation components
5. **Handlers**: Extract request handling
6. **Main**: Refactor main bot class

## ✅ **Success Criteria**
- Each file under 300 lines
- Clear single responsibility
- No circular dependencies
- All tests pass after each step
- Each step = atomic commit 