# -*- coding:utf-8 -*-
import appModuleHandler
import addonHandler
from NVDAObjects import NVDAObject
from controlTypes import Role, State
import api
from NVDAObjects.UIA import UIA
from scriptHandler import script
from ui import message
from ctypes import windll

addonHandler.initTranslation()


class Window(UIA):
    """
    Custom Window class to handle specific focus behaviors for enhanced accessibility.
    """

    def event_gainFocus(self):
        """
        This method is triggered when a window element gains focus.
        It adjusts the focus to specific child elements for better navigation.
        """
        if self.name.startswith('v2rayN') and self.children and self.children[1].role == Role.TOOLBAR and self.firstChild.role != Role.WINDOW:
            # Set focus to a specific child element in v2rayN application
            try:
                self.children[1].lastChild.setFocus()
            except Exception as e:
                api.getForegroundObject().children[1].lastChild.setFocus()
        elif (not self.name and len(self.children) == 1
              and self.firstChild.firstChild.firstChild.firstChild
              and self.firstChild.firstChild.firstChild.UIAAutomationId == 'menuSystemProxyClear'):
            # Focus on the designated child element in the application window
            self.firstChild.firstChild.firstChild.setFocus()


class Toggle(UIA):
    def event_stateChange(self):
        if self.UIAAutomationId == 'PART_Toggle':
            api.getForegroundObject(
            ).firstChild.firstChild.children[1].setFocus()


class AppModule(appModuleHandler.AppModule):
    """
    Custom app module to adjust element names and handle specific focus behaviors
    for enhanced accessibility.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isFocusedOnClose = False
        self.isFocusedOnEnableTon = False

    def maximize_window(self, hwnd):
        """
        Change window mode to Maximize using Handle
        """
        SW_MAXIMIZE = 3  # The code related to maximize
        windll.user32.ShowWindow(hwnd, SW_MAXIMIZE)

    def event_NVDAObject_init(self, obj):
        """
        Adjust the name of UI elements based on their role to improve the screen reader's output.
        """
        if obj.role == Role.MENUITEM:
            # Combine the menu item's first child's name (if available) with its role text
            name = obj.firstChild.name if not obj.name and obj.firstChild else obj.name
            role_text = obj.roleText or "Menu item"
            obj.name = f"{name} {role_text}"
        elif obj.role == Role.TOGGLEBUTTON:
            # Use the previous static text element or automation ID for toggle button naming
            name = (
                obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT
                else obj.UIAAutomationId if not obj.name and obj.UIAAutomationId
                else obj.name
            )
            if obj.UIAAutomationId == 'PART_Toggle':
                name = _("Settings")
            obj.name = name
        elif obj.role == Role.BUTTON:
            # Use the name of the first child element for buttons if no name is defined
            name = obj.firstChild.name if not obj.name and obj.firstChild else obj.UIAAutomationId[
                5:] if obj.UIAAutomationId and not obj.name else obj.name
            obj.name = name
        elif obj.role == Role.COMBOBOX:
            # Set combo box name using the previous element's name or adjusted automation ID
            name = (
                obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT
                else obj.UIAAutomationId[3:] if not obj.name and obj.UIAAutomationId
                else obj.name
            )
            obj.name = name
            # Remove default prefix from the value if it starts with "ServiceLib."
            obj.value = (
                "" if obj.value.startswith('ServiceLib.')
                else obj.value
            )
        elif obj.role == Role.EDITABLETEXT:
            # Use names of adjacent static text elements for editable text fields if available
            name = (
                obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT and obj.previous.name
                else obj.next.name if not obj.name and obj.next and obj.next.role == Role.STATICTEXT and obj.next.name
                else obj.UIAAutomationId if obj.UIAAutomationId and not obj.name
                else obj.name
            )
            if obj.UIAAutomationId == "txtServerFilter":
                name = obj.children[0].name
            obj.name = name
        elif obj.role == Role.LISTITEM:
            # Adjust name for list items
            name = (
                obj.firstChild.name if obj.firstChild and obj.firstChild.role == Role.STATICTEXT and obj.firstChild.name
                else f"{obj.children[1].name} {obj.children[2].name}" if len(obj.children) >= 3 and obj.children[1].role == Role.STATICTEXT and obj.children[1].name and obj.children[2].role == Role.STATICTEXT and obj.children[2].name
                else obj.firstChild.firstChild.name if obj.firstChild and obj.firstChild.firstChild and obj.firstChild.firstChild.role == Role.STATICTEXT and obj.firstChild.firstChild.name
                else obj.name
            )
            obj.name = (
                name[name.index('(') + 1:-1] if name.startswith('V3-') and name.endswith(')')
                else name
            )
        elif obj.role == Role.RADIOBUTTON:
            # Adjust name for radio buttons
            name = (
                obj.firstChild.name if (not obj.name or obj.name.startswith("ServiceLib.")) and obj.firstChild and obj.firstChild.role == Role.STATICTEXT and obj.firstChild.name
                else obj.name
            )
            obj.name = name
        elif obj.role == Role.DATAITEM:
            if obj.name.startswith("ServiceLib."):
                obj.name = ""
        elif obj.role == Role.UNKNOWN:
            if obj.name.startswith("Item: ServiceLib."):
                obj.name = ""
            obj.value = "" if obj.name == obj.value else obj.value
            obj.name = f"{obj.name}, "

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        """
        Add custom overlay classes for NVDA objects.
        If the object is a window, insert the custom Window class.
        """
        if isinstance(obj, UIA):
            if obj.role == Role.WINDOW:
                clsList.insert(0, Window)
            elif obj.role == Role.TOGGLEBUTTON:
                clsList.insert(0, Toggle)

    def event_focusEntered(self, obj: NVDAObject, nextHandler):
        if obj.role == Role.DATAGRID:
            message(f"{obj.UIAAutomationId[3:]} table")
        nextHandler()

    def event_gainFocus(self, obj: NVDAObject, nextHandler):
        if obj.role == Role.MENUITEM and obj.UIAAutomationId == 'menuClose':
            self.isFocusedOnClose = True
        else:
            self.isFocusedOnClose = False

        if obj.role == Role.TOGGLEBUTTON and obj.UIAAutomationId == 'togEnableTun':
            self.isFocusedOnEnableTon = True
        else:
            self.isFocusedOnEnableTon = False

        if obj.role == Role.WINDOW and obj.name.startswith("v2rayN"):
            hwnd = api.getForegroundObject().windowHandle
            self.maximize_window(hwnd)

        if obj.role == Role.DIALOG and obj.children:
            if obj.children[1].role == Role.TOOLBAR and obj.children[2].role == Role.DATAGRID:
                if len(obj.children[2].children) == 1:
                    obj.children[1].children[1].setFocus()
                else:
                    obj.children[2].children[1].children[0].setFocus()
            static_texts = [
                obj.name for obj in obj.children if obj.role == Role.STATICTEXT]
            if static_texts:
                for text in static_texts:
                    message(text)
            tab_control = next(
                (obj for obj in obj.children if obj.role == Role.TABCONTROL), None)
            if tab_control:
                tab_control.firstChild.setFocus()

        nextHandler()

    @ script(gesture="kb:tab")
    def script_handleTabKey(self, gesture):
        if self.isFocusedOnClose:
            obj = api.getFocusObject()
            try:
                targetChild = obj.parent.parent.next.children[5]
                if targetChild:
                    targetChild.setFocus()
            except Exception as e:
                pass
        else:
            gesture.send()

    @ script(gesture="kb:shift+tab")
    def script_handleShiftAndTabKey(self, gesture):
        if self.isFocusedOnEnableTon:
            obj = api.getFocusObject()
            try:
                targetChild = obj.parent.previous.children[-2].firstChild
                if targetChild:
                    targetChild.setFocus()
            except Exception as e:
                pass
        else:
            gesture.send()
