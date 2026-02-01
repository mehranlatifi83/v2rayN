# -*- coding:utf-8 -*-
import appModuleHandler
import addonHandler
import keyboardHandler
from NVDAObjects import NVDAObject
from controlTypes import Role, State
# import UIAHandler
# import comtypes
# from comtypes.client import CreateObject
# from UIAHandler import UIA_controlTypeIDs
import api
from NVDAObjects.UIA import UIA
import scriptHandler
from scriptHandler import script
from ui import message, browseableMessage
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
        if self.name and self.name.startswith('v2rayN') and self.children and len(self.children) >= 2 and self.children[1].role == Role.TOOLBAR and self.firstChild.role != Role.WINDOW:
            # Set focus to a specific child element in v2rayN application
            try:
                self.children[1].lastChild.setFocus()
            except Exception as e:
                api.getForegroundObject().children[1].children[1].lastChild.setFocus()
        elif (not self.name and len(self.children) == 1
              and self.firstChild.firstChild
              and self.firstChild.firstChild.firstChild
              and self.firstChild.firstChild.firstChild.UIAAutomationId == 'menuSystemProxyClear'):
            # Focus on the designated child element in the application window
            try:
                self.firstChild.firstChild.firstChild.setFocus()
            except Exception as e:
                pass


class Toggle(UIA):
    def event_stateChange(self):
        if State.PRESSED in self.states:
            message("Pressed")
            if self.UIAAutomationId and self.UIAAutomationId == 'PART_Toggle' and self.parent and self.parent.role and self.parent.role == Role.TOOLBAR:
                api.getForegroundObject(
                ).firstChild.firstChild.children[1].setFocus()
            if self.UIAAutomationId and self.UIAAutomationId == 'PART_Toggle' and self.parent and self.parent.role and self.parent.role == Role.PANE and self.parent.parent and self.parent.parent.role and self.parent.parent.role == Role.DIALOG:
                self.parent.parent.firstChild.children[1].setFocus()
        else:
            message("Not pressed")


class Combobox(UIA):
    @script(gesture="kb:downArrow")
    def script_focusToNextItem(self, gesture):
        keyboardHandler.KeyboardInputGesture.fromName("alt+downArrow").send()
        keyboardHandler.KeyboardInputGesture.fromName("downArrow").send()

    @script(gesture="kb:upArrow")
    def script_focusToPreviousItem(self, gesture):
        keyboardHandler.KeyboardInputGesture.fromName("alt+downArrow").send()
        keyboardHandler.KeyboardInputGesture.fromName("upArrow").send()


class AppModule(appModuleHandler.AppModule):
    """
    Custom app module to adjust element names and handle specific focus behaviors
    for enhanced accessibility.
    """

    def _findDescendant(self, root, role=None, automationId=None, maxDepth=30):
        """Recursively find a descendant matching role and/or UIAAutomationId."""
        if not root or maxDepth <= 0:
            return None

        try:
            if role is None or getattr(root, "role", None) == role:
                if automationId is None or getattr(root, "UIAAutomationId", None) == automationId:
                    return root
        except Exception:
            pass
        try:
            for child in getattr(root, "children", []) or []:
                found = self._findDescendant(child, role=role, automationId=automationId, maxDepth=maxDepth - 1)
                if found:
                    return found
        except Exception:
            pass
        return None

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
        if obj.role and obj.role == Role.MENUITEM:
            # Combine the menu item's first child's name (if available) with its role text
            name = obj.firstChild.name if not obj.name and obj.firstChild and obj.firstChild.name else obj.name
            role_text = obj.roleText or "Menu item"
            obj.name = f"{name} {role_text}"
        elif obj.role and obj.role == Role.TOGGLEBUTTON:
            # Use the previous static text element or automation ID for toggle button naming
            name = (
                obj.previous.name if not obj.name and obj.previous and obj.previous.role and obj.previous.role == Role.STATICTEXT
                else obj.UIAAutomationId if not obj.name and obj.UIAAutomationId
                else obj.name
            )
            if obj.UIAAutomationId == 'PART_Toggle':
                name = _("Settings")
            obj.name = name
        elif obj.role and obj.role == Role.BUTTON:
            # Use the name of the first child element for buttons if no name is defined
            name = obj.firstChild.name if not obj.name and obj.firstChild else obj.UIAAutomationId[
                5:] if obj.UIAAutomationId and not obj.name else obj.name
            obj.name = name
        elif obj.role and obj.role == Role.LINK:
            name = obj.firstChild.name if obj.firstChild and obj.firstChild.role and obj.firstChild.role == Role.STATICTEXT and obj.firstChild.name else obj.name
            obj.name = name
        elif obj.role and obj.role == Role.COMBOBOX:
            # Set combo box name using the previous element's name or adjusted automation ID
            name = (
                obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT
                else obj.UIAAutomationId[3:] if not obj.name and obj.UIAAutomationId
                else obj.name
            )
            obj.name = name
            # Remove default prefix from the value if it starts with "ServiceLib."
            obj.value = (
                "" if obj.value and obj.value.startswith('ServiceLib.')
                else obj.value
            )
        elif obj.role and obj.role == Role.EDITABLETEXT:
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
        elif obj.role and obj.role == Role.LISTITEM:
            # Adjust name for list items
            name = (
                obj.firstChild.name if obj.firstChild and obj.firstChild.role == Role.STATICTEXT and obj.firstChild.name
                else f"{obj.children[1].name} {obj.children[2].name} Pressed" if len(obj.children) >= 3 and obj.children[0].role == Role.TOGGLEBUTTON and State.PRESSED in obj.children[0].states and obj.children[1].role == Role.STATICTEXT and obj.children[1].name and obj.children[2].role == Role.STATICTEXT and obj.children[2].name
                else f"{obj.children[1].name} {obj.children[2].name} Not pressed" if len(obj.children) >= 3 and obj.children[0].role == Role.TOGGLEBUTTON and State.PRESSED not in obj.children[0].states and obj.children[1].role == Role.STATICTEXT and obj.children[1].name and obj.children[2].role == Role.STATICTEXT and obj.children[2].name
                else obj.firstChild.firstChild.name if obj.firstChild and obj.firstChild.firstChild and obj.firstChild.firstChild.role == Role.STATICTEXT and obj.firstChild.firstChild.name
                else obj.name
            )
            obj.name = (
                name[name.index('(') + 1:-1] if name.startswith('V3-') and name.endswith(')')
                else name
            )
        elif obj.role and obj.role == Role.RADIOBUTTON:
            # Adjust name for radio buttons
            name = (
                obj.firstChild.name if (not obj.name or obj.name.startswith("ServiceLib.")) and obj.firstChild and obj.firstChild.role == Role.STATICTEXT and obj.firstChild.name
                else obj.name
            )
            obj.name = name
        elif obj.role and obj.role == Role.TAB:
            name = obj.firstChild.name if obj.name.startswith(
                "System.Windows.Controls.TabItem") and obj.firstChild and obj.firstChild.role == Role.STATICTEXT else obj.name
            obj.name = name
        elif obj.role and obj.role == Role.DATAITEM:
            if obj.name and obj.name.startswith("ServiceLib."):
                obj.name = ""
        elif obj.role == Role.UNKNOWN:
            if obj.name and obj.name.startswith("Item: ServiceLib."):
                obj.name = ""
            obj.value = "" if obj.name and obj.value and obj.name == obj.value else obj.value
            obj.name = f"{obj.name}, "

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        """
        Add custom overlay classes for NVDA objects.
        """
        if isinstance(obj, UIA):
            if obj.role and obj.role == Role.WINDOW:
                clsList.insert(0, Window)
            elif obj.role and obj.role == Role.TOGGLEBUTTON:
                clsList.insert(0, Toggle)
            elif obj.role and obj.role == Role.COMBOBOX:
                clsList.insert(0, Combobox)

    def event_focusEntered(self, obj: NVDAObject, nextHandler):
        if obj.role and obj.role == Role.DATAGRID:
            message(f"{obj.UIAAutomationId[3:]} table")
        nextHandler()

    def event_gainFocus(self, obj: NVDAObject, nextHandler):
        if obj.role and obj.role == Role.WINDOW and obj.name and obj.name.startswith("v2rayN"):
            hwnd = api.getForegroundObject().windowHandle
            self.maximize_window(hwnd)

        if obj.role and obj.role == Role.DIALOG and obj.children:
            if len(obj.children) >= 3 and obj.children[1].role == Role.TOOLBAR and obj.children[2].role == Role.DATAGRID:
                if len(obj.children[2].children) == 1:
                    obj.children[1].children[1].setFocus()
                else:
                    obj.children[2].children[1].children[0].setFocus()
            static_texts = [
                obj.name for obj in obj.children if obj.role and obj.role == Role.STATICTEXT]
            if static_texts:
                for text in static_texts:
                    message(text)
            tab_control = next(
                (obj for obj in obj.children if obj.role and obj.role == Role.TABCONTROL), None)
            if tab_control:
                tab_control.firstChild.setFocus()

        nextHandler()

    @script(gesture="kb:tab")
    def script_handleTabKey(self, gesture):
        obj = api.getFocusObject()
        if obj.role and obj.role == Role.TOGGLEBUTTON and obj.UIAAutomationId and obj.UIAAutomationId == 'PART_Toggle' and obj.parent and obj.parent.role and obj.parent.role == Role.TOOLBAR:
            try:
                targetChild = obj.parent.children[1].firstChild
                if targetChild:
                    targetChild.setFocus()
            except Exception as e:
                pass

        elif obj.role and obj.role == Role.MENUITEM and obj.UIAAutomationId and obj.UIAAutomationId == 'menuClose':
            try:
                targetChild = obj.parent.parent.next.children[5]
                if targetChild:
                    targetChild.setFocus()
            except Exception as e:
                pass
        # elif obj.role and obj.role == Role.THUMB and obj.next.role and obj.next.role == Role.TABCONTROL and obj.next.UIAAutomationId == "tabMain1":
            # forground = api.getForegroundObject()
            # obj = next((obj for obj in forground.children if obj.role ==
                #    Role.TABCONTROL and obj.UIAAutomationId == "tabMain1"), None)
            # if obj and obj.firstChild and obj.firstChild.UIAElement:
                # uia = CreateObject("UIAutomationClient.CUIAutomation")
                # uiaElement = obj.firstChild.UIAElement

                # استفاده از متد GetCurrentPropertyValue برای دریافت مقدار درست
                # focusable_property = uiaElement.GetCurrentPropertyValue(
                # UIAHandler.UIA_IsKeyboardFocusablePropertyId)

                # if focusable_property is not None and not focusable_property:
                # UIAHandler.handler.setFocus(uiaElement)  # فعال کردن فوکوس
        elif obj.role and obj.role == Role.TAB and obj.parent and obj.parent.parent and obj.parent.parent.role and obj.parent.parent.role == Role.DIALOG:
            firstFocusableChild = next(
                (obj for obj in obj.children if State.FOCUSABLE in obj.states), None)
            if firstFocusableChild:
                if firstFocusableChild.role and firstFocusableChild.role == Role.PANE:
                    firstFocusableChild = next(
                        (obj for obj in firstFocusableChild.children if State.FOCUSABLE in obj.states), None)
                    if firstFocusableChild:
                        firstFocusableChild.setFocus()
                elif firstFocusableChild.role and firstFocusableChild.role == Role.DATAGRID:
                    firstFocusableChild = next(
                        (obj for obj in firstFocusableChild.children[1].children if State.FOCUSABLE in obj.states), None)
                    if firstFocusableChild:
                        firstFocusableChild.setFocus()
                else:
                    firstFocusableChild.setFocus()
        elif (obj.parent and obj.parent.role and obj.parent.role == Role.TAB) or (obj.parent and obj.parent.parent and obj.parent.parent.role and obj.parent.parent.role == Role.TAB) or (obj.parent and obj.parent.parent and obj.parent.parent.parent and obj.parent.parent.parent.role and obj.parent.parent.parent.role == Role.TAB):
            obj = obj.parent if obj.parent.role == Role.COMBOBOX or obj.parent.role == Role.LIST else obj
            lastFocusableObject = next(
                (o for o in obj.parent.children[::-1] if State.FOCUSABLE in o.states), None)
            if lastFocusableObject and lastFocusableObject == obj:
                obj = obj.parent if obj.parent.role == Role.TAB else obj.parent.parent if obj.parent.parent.role == Role.TAB else obj.parent.parent.parent if obj.parent.parent.parent.role == Role.TAB else obj
                obj = next((obj for obj in obj.parent.parent.children if obj.role and obj.role ==
                           Role.BUTTON and obj.UIAAutomationId and obj.UIAAutomationId == 'btnSave'), None)
                if obj:
                    obj.setFocus()
            else:
                gesture.send()
        elif obj.role and obj.role == Role.BUTTON and obj.UIAAutomationId and obj.UIAAutomationId == 'btnCancel' and obj.parent and obj.parent.role == Role.DIALOG:
            if obj.previous and obj.previous.previous and obj.previous.previous.previous and obj.previous.previous.previous.role and obj.previous.previous.previous.role == Role.TOOLBAR:
                obj.previous.previous.previous.children[1].firstChild.setFocus(
                )
            else:
                tab_control = next(
                    (obj for obj in obj.parent.children if obj.role == Role.TABCONTROL), None)
                if tab_control:
                    tab = next(
                        (obj for obj in tab_control.children if len(obj.children) > 1), None)
                    if tab:
                        tab.setFocus()
        elif obj.parent and obj.parent.role and obj.parent.role == Role.TOOLBAR and obj.parent.parent and obj.parent.parent.role and obj.parent.parent.role == Role.DIALOG:
            focusableObject = next(
                (o for o in obj.parent.children[::-1] if State.FOCUSABLE in o.states), None)
            if focusableObject and focusableObject == obj:
                if obj.parent.role == Role.TOOLBAR:
                    tab_control = next(
                        (obj for obj in obj.parent.parent.children if obj.role and obj.role == Role.TABCONTROL), None)
                    if tab_control:
                        tab = next(
                            (obj for obj in tab_control.children if len(obj.children) > 1), None)
                        if tab:
                            tab.setFocus()
            else:
                gesture.send()
        else:
            gesture.send()

    @script(gesture="kb:shift+tab")
    def script_handleShiftAndTabKey(self, gesture):
        obj = api.getFocusObject()
        if obj.role and obj.role == Role.MENUITEM and obj.name and obj.name == 'Configurations Menu item':
            try:
                targetChild = obj.parent.parent.lastChild
                if targetChild:
                    targetChild.setFocus()
            except Exception as e:
                pass

        elif obj.role and obj.role == Role.TOGGLEBUTTON and obj.UIAAutomationId and obj.UIAAutomationId == 'togEnableTun':
            try:
                targetChild = obj.parent.previous.children[-2].firstChild
                if targetChild:
                    targetChild.setFocus()
            except Exception as e:
                pass
        elif obj.role and obj.role == Role.TAB and obj.parent and obj.parent.parent and obj.parent.parent.role and obj.parent.parent.role == Role.DIALOG:
            obj = next(
                (obj for obj in obj.parent.parent.children[::-1] if obj.role == Role.BUTTON), None)
            if obj:
                if obj.previous and obj.previous.previous and obj.previous.previous.previous and obj.previous.previous.previous.role and obj.previous.previous.previous.role == Role.TOOLBAR:
                    obj.previous.previous.previous.lastChild.setFocus()
                else:
                    obj.setFocus()
        elif (obj.parent and obj.parent.role and obj.parent.role == Role.TAB) or (obj.parent and obj.parent.parent and obj.parent.parent.role and obj.parent.parent.role == Role.TAB) or (obj.parent and obj.parent.parent and obj.parent.parent.parent and obj.parent.parent.parent.role and obj.parent.parent.parent.role == Role.TAB):
            obj = obj.parent if obj.parent.role == Role.COMBOBOX or obj.parent.role == Role.LIST else obj
            firstFocusableObject = next(
                (o for o in obj.parent.children if State.FOCUSABLE in o.states), None)
            if firstFocusableObject and firstFocusableObject == obj:
                obj = obj.parent if obj.parent.role == Role.TAB else obj.parent.parent if obj.parent.parent.role == Role.TAB else obj.parent.parent.parent if obj.parent.parent.parent.role == Role.TAB else obj
                obj.setFocus()
            else:
                gesture.send()
        elif obj.role and obj.role == Role.BUTTON and obj.UIAAutomationId and obj.UIAAutomationId == 'btnSave' and obj.parent and obj.parent.role == Role.DIALOG:
            tab_control = next(
                (obj for obj in obj.parent.children if obj.role == Role.TABCONTROL), None)
            if tab_control:
                tab = next(
                    (obj for obj in tab_control.children if len(obj.children) > 1), None)
                if tab:
                    lastFocusableChild = next(
                        (obj for obj in tab.children[::-1] if State.FOCUSABLE in obj.states), None)
                    if lastFocusableChild:
                        if lastFocusableChild.role and lastFocusableChild.role == Role.PANE:
                            lastFocusableChild = next(
                                (obj for obj in lastFocusableChild.children[::-1] if State.FOCUSABLE in obj.states), None)
                            if lastFocusableChild:
                                lastFocusableChild.setFocus()
                        elif lastFocusableChild.role and lastFocusableChild.role == Role.DATAGRID:
                            lastFocusableChild = next(
                                (obj for obj in lastFocusableChild.children[1].children if State.FOCUSABLE in obj.states), None)
                            if lastFocusableChild:
                                lastFocusableChild.setFocus()
                        else:
                            lastFocusableChild.setFocus()
        elif obj.parent and obj.parent.parent and obj.parent.parent.role and obj.parent.parent.role == Role.TOOLBAR and obj.parent.parent.parent and obj.parent.parent.parent.role and obj.parent.parent.parent.role == Role.DIALOG:
            focusableObject = next(
                (o for o in obj.parent.parent.children if State.FOCUSABLE in o.states), None)
            if focusableObject and focusableObject == obj.parent:
                if obj.parent.parent.role == Role.TOOLBAR:
                    obj = next(
                        (obj for obj in obj.parent.parent.parent.children[::-1] if obj.role == Role.BUTTON), None)
                    if obj:
                        obj.setFocus()
            else:
                gesture.send()
        else:
            gesture.send()

    @script(gesture="kb:space")
    def script_handleSpace(self, gesture):
        obj = api.getFocusObject()
        if obj.role and obj.role == Role.MENUITEM or obj.role == Role.COMBOBOX:
            keyboardHandler.KeyboardInputGesture.fromName("enter").send()
        else:
            if obj.role and obj.role == Role.LISTITEM and len(obj.children) >= 3 and obj.children[0].role == Role.TOGGLEBUTTON and obj.children[1].role == Role.STATICTEXT and obj.children[2].role == Role.STATICTEXT:
                obj.children[0].setFocus()
                gesture.send()
                obj.setFocus()
                if State.PRESSED in obj.children[0].states:
                    message("Pressed")
                else:
                    message("Not pressed")
                return
            gesture.send()

    @script(gesture="kb:escape")
    def script_handleEscape(self, gesture):
        gesture.send()
        forground = api.getForegroundObject()
        if forground.children and len(forground.children) > 2 and forground.children[1].role == Role.TOOLBAR:
            forground.children[1].lastChild.setFocus()
        elif forground.children and len(forground.children) > 3 and forground.children[2] and forground.children[2].role == Role.TOOLBAR:
            forground.children[2].lastChild.setFocus()

    @script(gesture="kb:alt+p")
    def script_focusProfilesTable(self, gesture):
        fg = api.getForegroundObject()

        grid = self._findDescendant(fg, role=Role.DATAGRID, automationId="lstProfiles")
        if not grid:
            message(_("Profiles table not found"))
            return

        grid.setFocus()
        keyboardHandler.KeyboardInputGesture.fromName("tab").send()

    @script(gesture="kb:nvda+end")
    def script_readStatusbar(self, gesture):
        fg = api.getForegroundObject()

        running_server_display = self._findDescendant(
            fg, role=Role.STATICTEXT, automationId="txtRunningServerDisplay"
        )
        running_info_display = self._findDescendant(
            fg, role=Role.STATICTEXT, automationId="txtRunningInfoDisplay"
        )
        inbound_display = self._findDescendant(
            fg, role=Role.STATICTEXT, automationId="txtInboundDisplay"
        )
        inbound_lan_display = self._findDescendant(
            fg, role=Role.STATICTEXT, automationId="txtInboundLanDisplay"
        )

        lines = []

        if running_server_display and running_server_display.name:
            lines.append(running_server_display.name)

        if running_info_display and running_info_display.name:
            lines.append(running_info_display.name)

        if inbound_display and inbound_display.name:
            lines.append(_("Inbound: {text}").format(text=inbound_display.name))

        if inbound_lan_display and inbound_lan_display.name:
            lines.append(_("Inbound LAN: {text}").format(text=inbound_lan_display.name))

        if not lines:
            message(_("No status bar information found"))
            return

        # متن برای کپی (یک خط)
        clipboard_text = ", ".join(lines)

        # متن برای browse mode (چند خط، تمیزتر)
        browse_text = "\n".join(lines)

        repeat = scriptHandler.getLastScriptRepeatCount()

        # 3rd time browse mode
        if repeat >= 2:
            browseableMessage(
                browse_text,
                title=_("v2rayN status information")
            )

        # Second time: copy
        elif repeat >= 1:
            try:
                api.copyToClip(clipboard_text)
                message(_("Statusbar copied to clipboard"))
            except Exception:
                message(_("Failed to copy statusbar"))

        # First time: read only
        else:
            message(clipboard_text)

    @script(gesture="kb:alt+e")
    def script_changeTunMode(self, gesture):
        fg = api.getForegroundObject()

        tunToggle = self._findDescendant(fg, role=Role.TOGGLEBUTTON, automationId="togEnableTun")
        if not tunToggle:
            message(_("The enable tun button not found"))
            return

        tunToggle.doAction()

    def _speakSelectedItem(self, item):
        """Read selected item (name/value)"""
        if not item:
            return
        try:
            # If NVDA has a proper name for this object, speak it.
            if getattr(item, "name", None):
                message(item.name)
                return
        except Exception:
            pass
        try:
            # fallback
            message(str(item))
        except Exception:
            pass

    def _goToProfilesTable(self):
        """After selecting group, jump to profiles table like Alt+P."""
        try:
            keyboardHandler.KeyboardInputGesture.fromName("tab").send()
        except Exception:
            # If this fails, stay silent to avoid interrupting the user.
            pass

    def _hasOpenDialog(self):
        """True if any dialog is present under the foreground object."""
        fg = api.getForegroundObject()
        dlg = self._findDescendant(fg, role=Role.DIALOG, automationId=None, maxDepth=40)
        return bool(dlg)

    def _shouldHandleGroupSwitch(self):
        """Only handle Ctrl+Tab group switch when NO dialog is open."""
        return not self._hasOpenDialog()

    def _getLstGroupItems(self):
        fg = api.getForegroundObject()
        lst = self._findDescendant(fg, role=Role.LIST, automationId="lstGroup")
        if not lst:
            return None, []
        try:
            items = [c for c in (lst.children or []) if getattr(c, "role", None) in (Role.LISTITEM, Role.TAB, Role.UNKNOWN, Role.BUTTON)]
        except Exception:
            items = []
        # If the filtered list is empty, fall back to all children.
        if not items:
            try:
                items = list(lst.children or [])
            except Exception:
                items = []
        return lst, items

    def _findSelectedIndex(self, items):
        for i, it in enumerate(items):
            try:
                if State.SELECTED in it.states:
                    return i
            except Exception:
                pass
        return -1

    def _doSelectItem(self, item):
        """Prefer doAction; fallback to setFocus+enter if needed.
        After selection: speak it, then send Alt+P to jump to table.
        """
        if not item:
            return False

        selected = False

        try:
            item.doAction()
            selected = True
        except Exception:
            try:
                item.setFocus()
                keyboardHandler.KeyboardInputGesture.fromName("enter").send()
                selected = True
            except Exception:
                selected = False

        if selected:
            # After selection, state/name may update; try speaking the same item first.
            # (Optionally, you can re-fetch the selected item from the list.)
            try:
                # We try to read from the same item
                self._speakSelectedItem(item)
            except Exception:
                pass

            # Go to the table
            self._goToProfilesTable()

        return selected

    @script(gesture="kb:control+tab")
    def script_nextGroup(self, gesture):
        # Only when the dialog is not open
        if not self._shouldHandleGroupSwitch():
            gesture.send()
            return

        lst, items = self._getLstGroupItems()
        if not lst or not items:
            gesture.send()
            return

        sel = self._findSelectedIndex(items)

        # If nothing was selected → first
        if sel == -1:
            if not self._doSelectItem(items[0]):
                gesture.send()
            return

        # wrap
        nextIndex = 0 if sel >= (len(items) - 1) else (sel + 1)
        if not self._doSelectItem(items[nextIndex]):
            gesture.send()

    @script(gesture="kb:control+shift+tab")
    def script_prevGroup(self, gesture):
        # Only when the dialog is not open
        if not self._shouldHandleGroupSwitch():
            gesture.send()
            return

        lst, items = self._getLstGroupItems()
        if not lst or not items:
            gesture.send()
            return

        sel = self._findSelectedIndex(items)

        # If nothing was selected → Last
        if sel == -1:
            if not self._doSelectItem(items[-1]):
                gesture.send()
            return

        # wrap
        prevIndex = (len(items) - 1) if sel <= 0 else (sel - 1)
        if not self._doSelectItem(items[prevIndex]):
            gesture.send()

    @script(gesture="kb:alt+s")
    def script_openSystemProxyCombo(self, gesture):
        fg = api.getForegroundObject()

        cmb = self._findDescendant(fg, role=Role.COMBOBOX, automationId="cmbSystemProxy")
        if not cmb:
            message(_("System proxy combo not found"))
            return

        try:
            cmb.setFocus()
        except Exception:
            # If setFocus fails, fall back to sending the original gesture.
            gesture.send()
            return

        # Open the combo / move to the next option.
        try:
            keyboardHandler.KeyboardInputGesture.fromName("downArrow").send()
        except Exception:
            pass