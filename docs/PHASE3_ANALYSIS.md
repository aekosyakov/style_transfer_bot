# Phase 3: User Service Extraction Analysis

## 🎯 **Target Functions for user_service.py**

### **Language Management**
- `_get_user_language()` - line 227 (39 call sites)
- `redis_client.get_user_language()` - line 232
- `redis_client.set_user_language()` - lines 249, 1201

### **Premium Management** 
- `redis_client.is_user_premium()` - 10 call sites
- `redis_client.set_user_premium()` - lines 586, 611 (debug commands)

## 📍 **Call Site Analysis**

### **Language Function Call Sites (39 total)**
**Command Handlers:**
- start_command: 246, 274
- premium_command: 281  
- status_command: 294
- settings_command: 311
- feedback_command: 339
- about_command: 366
- invite_command: 400
- support_command: 432
- quota_command: 468
- style_command: 505
- video_command: 523  
- help_command: 540
- debug_premium_command: 583
- debug_revoke_command: 608

**Message Handlers:**
- handle_photo: 622, 652
- handle_document: 659, 704
- handle_text: 710
- handle_callback_query: 727

**UI Helpers:**
- _show_main_menu: 853
- _show_premium_options: 863
- _show_enhancement_menu: 892
- _show_upload_prompt: 903
- _show_help_message: 911

**Category/Option Handlers:**
- _handle_category_selection: 935
- _handle_option_selection: 1025, 1177

**Language/Menu Handlers:**
- _handle_language_change: 1201
- _show_referral_stats: 1237
- _show_faq: 1264
- _show_bug_report: 1293

**Action Handlers:**
- _handle_retry: 1325
- _handle_repeat_video: 1488
- _handle_restart: 1529
- _handle_animate_result: 1661

### **Premium Function Call Sites (10 total)**
- premium_command: 282
- status_command: 295, 317
- debug_premium_command: 586
- debug_revoke_command: 611
- _get_main_menu_keyboard: 819
- _get_enhancement_keyboard: 835
- _handle_category_selection: 936
- _handle_option_selection: 1026
- _handle_language_change: 1210

## 🚨 **Risk Assessment**

**HIGH COMPLEXITY**: 49 total call sites to update
**CRITICAL FUNCTIONS**: Language detection affects every user interaction
**DEPENDENCY CHAIN**: redis_client → localization → UI components

## 📋 **Migration Strategy**

### **Phase 3A: user_service.py Creation**
1. Create service with all user-related methods
2. Keep original methods as wrappers initially  
3. Unit test the service thoroughly

### **Phase 3B: Gradual Migration**
1. Update method calls in groups:
   - Command handlers (15 sites)
   - Message handlers (6 sites) 
   - UI helpers (5 sites)
   - Action handlers (remaining sites)
2. Test after each group
3. Remove wrapper methods last

### **Phase 3C: Integration Testing**
1. Test full user workflow: language detection → premium check → UI display
2. Test language switching
3. Test premium upgrade/downgrade

## ✅ **Success Criteria**
- All 49 call sites updated correctly
- User service works in isolation (unit tests)
- Full user workflow works (integration test)
- No regression in existing functionality 