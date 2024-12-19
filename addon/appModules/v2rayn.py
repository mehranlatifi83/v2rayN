# -*- coding:utf-8 -*-
import appModuleHandler
from NVDAObjects import NVDAObject
from controlTypes import Role
from ui import message
from scriptHandler import script
import api
import time


class AppModule(appModuleHandler.AppModule):
    def event_gainFocus(self, obj: NVDAObject, nextHandler):
        if not obj.isFocusable:
            obj.isFocusable = True

        if obj.role == Role.MENUITEM:
            name = obj.firstChild.name if not obj.name and obj.firstChild else obj.name
            role_text = obj.roleText or _("Menu item")
            obj.name = f"{name} {role_text}"
        elif obj.role == Role.TOGGLEBUTTON:
            name = obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT else obj.UIAAutomationId if not obj.name and obj.UIAAutomationId else obj.name
            obj.name = name
        elif obj.role == Role.BUTTON:
            name = obj.firstChild.name if not obj.name and obj.firstChild else obj.name
            obj.name = name
        elif obj.role == Role.COMBOBOX:
            name = obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT else obj.UIAAutomationId[
                3:] if not obj.name and obj.UIAAutomationId else obj.name
            obj.name = name
        elif obj.role == Role.EDITABLETEXT:
            name = obj.previous.name if not obj.name and obj.previous and obj.previous.role == Role.STATICTEXT and obj.previous.name else obj.next.name if not obj.name and obj.next and obj.next.role == Role.STATICTEXT and obj.next.name else obj.name
            obj.name = name
        if obj.role == Role.DIALOG and obj.name == 'Subscription group settings':
            message(obj.lastChild.role)
            if obj.lastChild.lastChild.role == Role.STATICTEXT and obj.lastChild.lastChild.name == 'Sort':
                obj = next(
                    (child.firstChild for child in obj.children if child.role == Role.TOOLBAR), obj)
                obj.setFocus()
        if obj.role == Role.WINDOW:
            obj.firstChild.firstChild.firstChild.setFocus()
        nextHandler()
