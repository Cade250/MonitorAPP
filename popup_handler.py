import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException

class PopupHandler:
    """通用弹窗处理器，专门处理中文弹窗"""
    
    def __init__(self, driver):
        self.driver = driver
    
    def handle_popups(self, max_attempts=5):
        """检测并关闭绝大多数中文弹窗"""
        for attempt in range(max_attempts):
            try:
                print(f"弹窗检测第 {attempt + 1} 轮...")
                
                # 第一阶段：通过中文文本内容检测弹窗按钮
                text_patterns = [
                    # 确认类按钮
                    "确定", "确认", "好的", "知道了", "我知道了", "明白了",
                    "同意", "允许", "接受", "继续", "下一步", "立即体验",
                    "开始使用", "马上体验", "立即开始", "去设置",
                    # 取消/关闭类按钮
                    "取消", "关闭", "跳过", "稍后", "暂不", "不了", "以后再说",
                    "暂时不用", "下次再说", "忽略", "不再提示", "我再想想",
                    # 更新相关
                    "暂不更新", "稍后更新", "取消更新", "忽略更新", "下次更新",
                    # 权限相关
                    "始终允许", "仅在使用时允许", "拒绝", "禁止", "不允许",
                    # 通知相关
                    "不开启", "暂不开启", "关闭通知", "稍后设置",
                    # 广告相关
                    "跳过广告", "关闭广告", "不感兴趣"
                ]
                
                found_and_closed = False
                
                # 遍历文本模式
                for text in text_patterns:
                    try:
                        # 精确匹配
                        elements = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR, 
                            f'new UiSelector().text("{text}")'
                        )
                        if elements and self._try_click_element(elements[0], f"文本匹配: {text}"):
                            found_and_closed = True
                            break
                        
                        # 包含匹配
                        elements = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR, 
                            f'new UiSelector().textContains("{text}")'
                        )
                        if elements and self._try_click_element(elements[0], f"文本包含: {text}"):
                            found_and_closed = True
                            break
                            
                    except Exception:
                        continue
                
                if found_and_closed:
                    time.sleep(2)
                    continue
                
                # 第二阶段：通过通用资源ID检测弹窗按钮
                resource_id_patterns = [
                    "close", "cancel", "dismiss", "skip", "later", "ok", "confirm",
                    "btn_close", "btn_cancel", "btn_dismiss", "btn_skip", "btn_ok",
                    "iv_close", "iv_cancel", "img_close", "image_close",
                    "update_cancel", "dialog_cancel", "popup_close", "modal_close",
                    "negative", "positive", "neutral"
                ]
                
                for res_id in resource_id_patterns:
                    try:
                        # 部分匹配
                        elements = self.driver.find_elements(
                            AppiumBy.XPATH, 
                            f"//*[contains(@resource-id, '{res_id}')]"
                        )
                        
                        if elements and self._try_click_element(elements[0], f"资源ID: {res_id}"):
                            found_and_closed = True
                            break
                            
                    except Exception:
                        continue
                
                if found_and_closed:
                    time.sleep(2)
                    continue
                
                # 第三阶段：通过className和中文description检测
                class_desc_patterns = [
                    # 图片按钮（通常是关闭按钮）
                    ('android.widget.ImageView', ['关闭', '取消', '返回']),
                    ('android.widget.ImageButton', ['关闭', '取消', '返回']),
                    # 文本按钮
                    ('android.widget.Button', ['确定', '取消', '关闭', '跳过', '同意', '允许']),
                    ('android.widget.TextView', ['确定', '取消', '关闭', '跳过', '同意', '允许'])
                ]
                
                for class_name, descriptions in class_desc_patterns:
                    for desc in descriptions:
                        try:
                            elements = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                f'new UiSelector().className("{class_name}").description("{desc}")'
                            )
                            if elements and self._try_click_element(elements[0], f"类名+描述: {class_name}[{desc}]"):
                                found_and_closed = True
                                break
                        except Exception:
                            continue
                    if found_and_closed:
                        break
                
                if found_and_closed:
                    time.sleep(2)
                    continue
                
                # 第四阶段：检测可点击的小尺寸元素（通常是关闭按钮）
                try:
                    # 查找小尺寸的可点击元素，通常是右上角的关闭按钮
                    small_clickable_elements = self.driver.find_elements(
                        AppiumBy.XPATH,
                        "//*[@clickable='true' and string-length(@text)=0]"
                    )
                    
                    for element in small_clickable_elements:
                        try:
                            # 获取元素位置和大小
                            location = element.location
                            size = element.size
                            
                            # 检查是否是小尺寸元素（可能是关闭按钮）
                            if (size['width'] <= 100 and size['height'] <= 100 and 
                                location['x'] > 200):  # 通常关闭按钮在右侧
                                
                                if self._try_click_element(element, "小尺寸可点击元素（疑似关闭按钮）"):
                                    found_and_closed = True
                                    break
                        except Exception:
                            continue
                            
                except Exception:
                    pass
                
                if found_and_closed:
                    time.sleep(2)
                    continue
                
                # 第五阶段：检测Dialog类型的弹窗
                try:
                    dialog_elements = self.driver.find_elements(
                        AppiumBy.XPATH,
                        "//*[contains(@class, 'Dialog') or contains(@class, 'AlertDialog')]"
                    )
                    
                    if dialog_elements:
                        # 在Dialog中查找按钮
                        for dialog in dialog_elements:
                            try:
                                buttons = dialog.find_elements(
                                    AppiumBy.XPATH,
                                    ".//android.widget.Button"
                                )
                                
                                # 优先点击取消、关闭类按钮
                                for button in buttons:
                                    button_text = button.text
                                    if any(keyword in button_text for keyword in ["取消", "关闭", "跳过", "稍后"]):
                                        if self._try_click_element(button, f"Dialog按钮: {button_text}"):
                                            found_and_closed = True
                                            break
                                
                                if found_and_closed:
                                    break
                                    
                            except Exception:
                                continue
                                
                except Exception:
                    pass
                
                if found_and_closed:
                    time.sleep(2)
                    continue
                
                # 第六阶段：使用返回键尝试关闭弹窗
                try:
                    print("尝试使用返回键关闭弹窗...")
                    self.driver.back()
                    time.sleep(1)
                    found_and_closed = True
                except Exception:
                    pass
                
                if not found_and_closed:
                    print(f"第 {attempt + 1} 轮未检测到弹窗，结束检测。")
                    return
                    
            except Exception as e:
                print(f"弹窗处理第 {attempt + 1} 轮发生错误: {e}")
                continue
        
        print(f"完成 {max_attempts} 轮弹窗检测。")
    
    def _try_click_element(self, element, description):
        """尝试点击元素的辅助方法"""
        try:
            if element.is_enabled() and element.is_displayed():
                element.click()
                print(f"成功关闭弹窗: {description}")
                return True
        except Exception as e:
            print(f"点击元素失败 ({description}): {e}")
        return False
    
    def quick_popup_check(self):
        """快速弹窗检查，用于操作间隙的简单检测"""
        try:
            # 快速检查常见的弹窗文本
            quick_texts = ["确定", "取消", "关闭", "跳过", "知道了", "同意"]
            
            for text in quick_texts:
                try:
                    elements = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR, 
                        f'new UiSelector().text("{text}")'
                    )
                    if elements and self._try_click_element(elements[0], f"快速检测: {text}"):
                        time.sleep(1)
                        return True
                except Exception:
                    continue
            
            return False
        except Exception:
            return False