# Author-koki yamane
# Description-trochoid curve

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math


def epicycloid(theta, r_c, r_m, r_d=None):
    if r_d is None:
        r_d = r_m
    x = (r_c + r_m) * math.cos(theta) - r_d * math.cos((r_c + r_m) / r_m * theta)
    y = (r_c + r_m) * math.sin(theta) - r_d * math.sin((r_c + r_m) / r_m * theta)
    return x, y


def hypercycloid(theta, r_c, r_m, r_d=None):
    if r_d is None:
        r_d = r_m
    x = (r_c - r_m) * math.cos(theta) + r_d * math.cos(-(r_c - r_m) / r_m * theta)
    y = (r_c - r_m) * math.sin(theta) + r_d * math.sin(-(r_c - r_m) / r_m * theta)
    return x, y


def trochoid(theta, r, teeth):
    r_m = r / teeth / 2
    if theta % ((2 * math.pi) / teeth) < math.pi / teeth:
        return epicycloid(theta, r, r_m, r_m)
    else:
        return hypercycloid(theta, r, r_m, r_m)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()

        design = app.activeProduct

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create a new sketch on the xy plane.
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        # Create an object collection for the points.
        points = adsk.core.ObjectCollection.create()

        r = 10
        teeth = 7
        num = 200
        for theta in [i / num * 2 * math.pi for i in range(0, num + 1)]:
            x, y = trochoid(theta, r, teeth)
            points.add(adsk.core.Point3D.create(x, y, 0))

        # Create the spline.
        sketch.sketchCurves.sketchFittedSplines.add(points)

    except BaseException:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
