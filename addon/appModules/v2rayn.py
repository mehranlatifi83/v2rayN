# -*- coding:utf-8 -*-
import appModuleHandler
from NVDAObjects import NVDAObject
from controlTypes import Role
import api
from NVDAObjects.UIA import UIA
from scriptHandler import script


class Window(UIA):
    """
    Custom Window class to handle specific focus behaviors for enhanced accessibility.
    """

    def event_gainFocus(self):
        """
        This method is triggered when a window element gains focus.
        It adjusts the focus to specific child elements for better navigation.
        """
        if self.name.startswith('v2rayN') and self.firstChild.role != Role.WINDOW:
            # Set focus to a specific child element in v2rayN application
            self.children[1].firstChild.setFocus()
        elif (
            not self.name and len(self.children) == 1 and
            self.firstChild.firstChild.firstChild.firstChild and
            self.firstChild.firstChild.firstChild.firstChild.name == "Clear system proxy"
        ):
            # Focus on the designated child element in the application window
            self.firstChild.firstChild.firstChild.setFocus()


class AppModule(appModuleHandler.AppModule):
    """
    Custom app module to adjust element names and handle specific focus behaviors
    for enhanced accessibility.
    """

    def event_NVDAObject_init(self, obj):
        """
        Adjust the name of UI elements based on their role to improve the screen reader's output.
        """
        if obj.role == Role.MENUITEM:
            # Combine the menu item's first child's name (if available) with its role text
            name = obj.firstChild.name if not obj.name and obj.firstChild else obj.name
            role_text = obj.roleText or _("Menu item")
            obj.name = f"{name} {role_text}"
        elif obj.role == Role.TOGGLEBUTTON:
            # Use the previous static text element or automation ID for toggle button naming
            name = (
                obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT
                else obj.UIAAutomationId if not obj.name and obj.UIAAutomationId
                else obj.name
            )
            obj.name = name
        elif obj.role == Role.BUTTON:
            # Use the name of the first child element for buttons if no name is defined
            name = obj.firstChild.name if not obj.name and obj.firstChild else obj.name
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
                else obj.name
            )
            obj.name = name
        elif obj.role == Role.LISTITEM:
            # Adjust name for list items
            name = (
                obj.firstChild.name if obj.firstChild and obj.firstChild.role == Role.STATICTEXT and obj.firstChild.name
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

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        """
        Add custom overlay classes for NVDA objects.
        If the object is a window, insert the custom Window class.
        """
        if obj.role == Role.WINDOW:
            clsList.insert(0, Window)
