# Author-koki yamane
# Description-trochoid curve

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math


defaultOuterR = 10
defaultOuterTeeth = 7
defaultClearance = 0.01
defaultHeight = 10
defaultOuterThickness = 5


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


class TrochoidCurve():
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

    def make_trochoid_curve(self, sketch, point_num=200):
        # Create an object collection for the points.
        points = adsk.core.ObjectCollection.create()

        for theta in [i / point_num * 2 *
                      math.pi for i in range(0, point_num + 1)]:
            x, y = self.trochoid(theta, self.r, self.teeth)
            points.add(adsk.core.Point3D.create(x, y, 0))

        # Create the spline.
        sketch.sketchCurves.sketchFittedSplines.add(points)


class InnerGear():
    def __init__(self, r, teeth, height) -> None:
        self.r = r
        self.teeth = teeth
        self.height = height

    def buildInnerGear(self):
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox(
                'New component failed to create',
                'New Component Failed')
            return

        # Create a new sketch on the xy plane.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        # Draw the trochoid curve.
        TrochoidCurve(r=self.r, teeth=self.teeth).make_trochoid_curve(sketch)

        # Create an extrusion.
        extInput = newComp.features.extrudeFeatures.createInput(
            sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(self.height)
        extInput.setDistanceExtent(False, distance)
        ext = newComp.features.extrudeFeatures.add(extInput)


class OuterGear():
    def __init__(self, r, teeth, height, thickness) -> None:
        self.r = r
        self.teeth = teeth
        self.height = height
        self.thickness = thickness

    def buildOuterGear(self):
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox(
                'New component failed to create',
                'New Component Failed')
            return

        # Create a new sketch on the xy plane.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        # Draw the trochoid curve.
        center = adsk.core.Point3D.create(0, 0, 0)
        sketch.sketchCurves.sketchCircles.addByCenterRadius(
            center, self.r + self.thickness)
        TrochoidCurve(r=self.r, teeth=self.teeth).make_trochoid_curve(sketch)

        # Create an extrusion.
        extInput = newComp.features.extrudeFeatures.createInput(
            sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(self.height)
        extInput.setDistanceExtent(False, distance)
        ext = newComp.features.extrudeFeatures.add(extInput)


class TrochoidPump():
    def __init__(self) -> None:
        self.outer_r = defaultOuterR
        self.outer_teeth = defaultOuterTeeth
        self.clearance = defaultClearance
        self.height = defaultHeight
        self.thickness = defaultOuterThickness

    def buildTrochoidPump(self):
        inner_teeth = self.outer_teeth - 1
        tooth_h = self.outer_r / (2 * self.outer_teeth)
        inner_r = self.outer_r - 2 * (tooth_h + self.clearance)

        innerGear = InnerGear(inner_r, inner_teeth, self.height)
        outerGear = OuterGear(
            self.outer_r,
            self.outer_teeth,
            self.height,
            self.thickness)

        innerGear.buildInnerGear()
        outerGear.buildOuterGear()


# input dialog setting
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command

            # class to using input data
            onExecute = MyCommandExecuteHandler()
            cmd.execute.add(onExecute)

            # validation class
            onValidateInputs = MyCommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)

            # destroy class
            onDestroy = MyCommandDestroyHandler()
            cmd.destroy.add(onDestroy)

            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onDestroy)
            handlers.append(onValidateInputs)

            # define the inputs
            inputs = cmd.commandInputs
            inputs.addValueInput(
                'outer_r', 'outer radius', 'mm', adsk.core.ValueInput.createByReal(defaultOuterR / 10))
            inputs.addValueInput(
                'outer_teeth', 'outer teeth number', '', adsk.core.ValueInput.createByReal(defaultOuterTeeth))
            inputs.addValueInput(
                'height', 'height', 'mm', adsk.core.ValueInput.createByReal(defaultHeight / 10))
            inputs.addValueInput(
                'clearance', 'clearance', 'mm', adsk.core.ValueInput.createByReal(defaultClearance / 10))
            inputs.addValueInput(
                'outer_thickness', 'outer thickness', 'mm', adsk.core.ValueInput.createByReal(defaultOuterThickness / 10))

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

            unitsMgr = app.activeProduct.unitsManager

            trochoidPump = TrochoidPump()

            input = inputs.itemById('outer_r')
            trochoidPump.outer_r = unitsMgr.evaluateExpression(
                input.expression, "mm")

            input = inputs.itemById('outer_teeth')
            trochoidPump.outer_teeth = unitsMgr.evaluateExpression(
                input.expression, "")

            input = inputs.itemById('height')
            trochoidPump.height = unitsMgr.evaluateExpression(
                input.expression, "mm")

            input = inputs.itemById('outer_thickness')
            trochoidPump.thickness = unitsMgr.evaluateExpression(
                input.expression, "mm")

            trochoidPump.buildTrochoidPump()

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

            r_input = inputs.itemById('outer_r')

            unitsMgr = app.activeProduct.unitsManager
            r = unitsMgr.evaluateExpression(
                r_input.expression, "mm")

            if r == 0:
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
