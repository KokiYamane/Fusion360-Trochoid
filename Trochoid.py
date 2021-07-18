# Author-koki yamane
# Description-trochoid curve

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math


# global set of event handlers to keep them referenced for the duration of
# the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface


def createNewComponent():
    # Get the active design.
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component


class Trochoid():
    def __init__(self, r=10, teeth=7) -> None:
        self.r = r
        self.teeth = teeth

    def epicycloid(self, theta, r_c, r_m, r_d=None):
        if r_d is None:
            r_d = r_m
        x = (r_c + r_m) * math.cos(theta) - r_d * \
            math.cos((r_c + r_m) / r_m * theta)
        y = (r_c + r_m) * math.sin(theta) - r_d * \
            math.sin((r_c + r_m) / r_m * theta)
        return x, y

    def hypercycloid(self, theta, r_c, r_m, r_d=None):
        if r_d is None:
            r_d = r_m
        x = (r_c - r_m) * math.cos(theta) + r_d * \
            math.cos(-(r_c - r_m) / r_m * theta)
        y = (r_c - r_m) * math.sin(theta) + r_d * \
            math.sin(-(r_c - r_m) / r_m * theta)
        return x, y

    def trochoid(self, theta, r, teeth):
        r_m = r / teeth / 2
        if theta % ((2 * math.pi) / teeth) < math.pi / teeth:
            return self.epicycloid(theta, r, r_m, r_m)
        else:
            return self.hypercycloid(theta, r, r_m, r_m)

    def make_trochoid_curve(self, point_num=200):
        newComp = createNewComponent()

        # Create a new sketch on the xy plane.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        # Create an object collection for the points.
        points = adsk.core.ObjectCollection.create()

        for theta in [i / point_num * 2 *
                      math.pi for i in range(0, point_num + 1)]:
            x, y = self.trochoid(theta, self.r, self.teeth)
            points.add(adsk.core.Point3D.create(x, y, 0))

        # Create the spline.
        sketch.sketchCurves.sketchFittedSplines.add(points)


# input dialog setting
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command

            # use input data
            onExecute = MyCommandExecuteHandler()
            cmd.execute.add(onExecute)

            # validation
            onValidateInputs = MyCommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)

            # destroy
            onDestroy = MyCommandDestroyHandler()
            cmd.destroy.add(onDestroy)

            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onDestroy)
            handlers.append(onValidateInputs)

            # define the inputs
            inputs = cmd.commandInputs

            inputs.addValueInput(
                'r', 'r', 'mm', adsk.core.ValueInput.createByReal(1))

            inputs.addValueInput(
                'teeth', 'teeth', '', adsk.core.ValueInput.createByReal(7))

        except BaseException:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# class that get data from input dialog
class MyCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            command = args.firingEvent.sender
            inputs = command.commandInputs

            r_input = inputs.itemById('r')

            unitsMgr = app.activeProduct.unitsManager
            r = unitsMgr.evaluateExpression(
                r_input.expression, "mm")

            # make trochoid curve
            Trochoid(r=r, teeth=7).make_trochoid_curve()

            args.isValidResult = True

        except BaseException:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# validate data from input dialog
class MyCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            command = args.firingEvent.sender
            inputs = command.commandInputs

            r = inputs.itemById('r')

            unitsMgr = app.activeProduct.unitsManager
            myValue = unitsMgr.evaluateExpression(
                r.expression, "mm")

            if myValue == 0:
                args.areInputsValid = False
            else:
                args.areInputsValid = True
        except BaseException:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# destroy input dialog
class MyCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            adsk.terminate()
        except BaseException:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox(
                'It is not supported in current workspace, please change to MODEL workspace and try again.')
            return

        # input dialog
        commandId = 'Trochoid'
        commandName = 'Trochoid'
        commandDescription = 'Trochoid'
        cmdDef = ui.commandDefinitions.itemById(commandId)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(
                commandId, commandName, commandDescription)
        onCommandCreated = MyCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns,
        # because we are waiting for event handlers to fire
        adsk.autoTerminate(False)

    except BaseException:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
