# -*- coding:utf-8 -*-
import appModuleHandler
from NVDAObjects import NVDAObject
from controlTypes import Role
import api


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
        elif obj.role == Role.EDITABLETEXT:
            # Use names of adjacent static text elements for editable text fields if available
            name = (
                obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT and obj.previous.name
                else obj.next.name if not obj.name and obj.next and obj.next.role == Role.STATICTEXT and obj.next.name
                else obj.name
            )
            obj.name = name

    def event_gainFocus(self, obj: NVDAObject, nextHandler):
        """
        Set focus on a specific child element when the main application window is activated.
        This applies only if the child element matches the defined condition.
        """
        if (
            obj.role == Role.WINDOW and
            obj.firstChild.firstChild.firstChild.firstChild and
            obj.firstChild.firstChild.firstChild.firstChild.name == "Clear system proxy"
        ):
            # Focus on the designated child element in the application window
            obj.firstChild.firstChild.firstChild.setFocus()
        nextHandler()  # Call the default focus handling logic
