from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom

class AppView:
    def __init__(self, _model=[], _reshape=[]):
        self.model = _model  # owning model object
        self.reshape = _reshape  # curve reshape object

        # Defined colors
        self.colorBackground = [1.00, 1.00, 1.00]  # white
        self.colorSelection = [1.00, 0.00, 0.00]  # red
        self.colorPoint = [0.00, 0.00, 0.50]  # dark blue
        self.colorPointSelection = [1.00, 0.00, 0.00]  # red
        self.colorSegment = [0.00, 0.00, 0.00]  # black
        self.colorSegmentSelection = [1.00, 0.00, 0.00]  # red
        self.colorPatch = [0.75, 0.75, 0.75]  # light gray
        self.colorPatchSelection = [1.00, 0.75, 0.75]  # light red
        self.colorCollecting = [1.00, 0.00, 0.00]  # red
        self.colorGrid = [0.00, 0.00, 0.00]  # black
        self.colorSdvPoint = [0.00, 0.00, 0.50]  # dark blue
        self.colorMesh = [0.00, 0.00, 0.75]  # light blue

    # ---------------------------------------------------------------------
    def setModel(self, _model):
        self.model = _model

    # ---------------------------------------------------------------------
    def setReshape(self, _reshape):
        self.reshape = _reshape

    # ---------------------------------------------------------------------
    def isEmpty(self):
        return (self.model is None) or (self.model.isEmpty())

    # ---------------------------------------------------------------------
    def getPoints(self):
        points = []
        if self.model.isEmpty():
            return points
        segments = self.model.getSegments()
        for seg in segments:
            pt = seg.getPntInit()
            points.append(pt)
            pt = seg.getPntEnd()
            points.append(pt)
        return points

    # ---------------------------------------------------------------------
    def getSegments(self):
        return self.model.getSegments()

    # ---------------------------------------------------------------------
    def getPatches(self):
        return self.model.getPatches()

    # ---------------------------------------------------------------------
    def isPointSelected(self, _pnt):
        return False

    # ---------------------------------------------------------------------
    def isSegmentSelected(self, _seg):
        if _seg.isSelected():
            return True
        return False

    # ---------------------------------------------------------------------
    def isPatchSelected(self, _ptch):
        if _ptch.isSelected():
            return True
        return False

    # ---------------------------------------------------------------------
    def getPointLoc(self, _pnt):
        return _pnt

    # ---------------------------------------------------------------------
    def getSegmentPts(self, _seg):
        return _seg.getPolylinePts()

    # ---------------------------------------------------------------------
    def getPatchPts(self, _ptch):
        return _ptch.getPoints()

    # ---------------------------------------------------------------------
    def getSegmentSdvPts(self, _seg):
        return []

    # ---------------------------------------------------------------------
    def getPatchMesh(self, _ptch):
        return [], []

    # ---------------------------------------------------------------------
    def getCurveSegment(self, _curve):
        segments = self.model.getSegments()
        for seg in segments:
            if seg.curve == _curve:
                return seg
        return []

    # ---------------------------------------------------------------------
    def unselectAll(self):
        if self.model.isEmpty():
            return
        segments = self.model.getSegments()
        for seg in segments:
            seg.setSelected(False)
        patches = self.model.getPatches()
        for ptch in patches:
            ptch.setSelected(False)

    # ---------------------------------------------------------------------
    def selectPick(self, _x,  _y, _tol, _shiftkey):
        self.model.setCurrTol(_tol)
        if self.selectPickPoints(_x, _y, _tol, _shiftkey):
            return
        if self.selectPickSegments(_x, _y, _tol, _shiftkey):
            return
        if self.selectPickPatches(_x, _y, _shiftkey):
            return

    # ---------------------------------------------------------------------
    def selectPickPoints(self, _x, _y, _tol, _shiftkey):
            return False

    # ---------------------------------------------------------------------
    def selectPickSegments(self, _x, _y, _tol, _shiftkey):
        if self.model.isEmpty():
            return False

        oneSegmentSelected = False

        # Select segment
        id_target = -1
        dmin = _tol
        segments = self.model.getSegments()
        for i in range(0, len(segments)):
            # Compute distance between given point and current
            # segment and update minimum distance
            status, xC, yC, d = segments[i].closestPoint(_x, _y)
            if status:
                if d < dmin:
                    dmin = d
                    id_target = i

        # Revert selection of picked segment
        if id_target > -1:
            if segments[id_target].isSelected():
                segments[id_target].setSelected(False)
            else:
                segments[id_target].setSelected(True)
                oneSegmentSelected = True

        if not _shiftkey:
            # If shift key is not pressed, unselect all segment except
            # the picked one (if there was one selected)
            for i in range(0, len(segments)):
                if (id_target == -1) or (i != id_target):
                    segments[i].setSelected(False)

        return oneSegmentSelected

    # ---------------------------------------------------------------------
    def selectPickPatches(self, _x,  _y, _shiftkey):
        if self.model.isEmpty():
            return False

        pickPnt = Pnt2D(_x, _y)
        onePatchSelected = False

        # Select patch
        id_target = -1
        patches = self.model.getPatches()
        for i in range(0, len(patches)):
            ptch = patches[i]
            if CompGeom.isPointInPolygon( ptch.getPoints(), pickPnt):
                id_target = i
                break

        # Revert selection of picked patch
        if id_target > -1:
            if patches[id_target].isSelected():
                patches[id_target].setSelected(False)
            else:
                patches[id_target].setSelected(True)
                onePatchSelected = True

        if not _shiftkey:
            # If shift key is not pressed, unselect all patch except
            # the picked one (if there was one selected)
            for i in range(0, len(patches)):
                if (id_target == -1) or (i != id_target):
                    patches[i].setSelected(False)

        return onePatchSelected

    # ---------------------------------------------------------------------
    def selectFence(self, _xmin, _xmax, _ymin, _ymax, _shiftkey):
        self.selectFencePoints(_xmin, _xmax, _ymin, _ymax, _shiftkey)
        self.selectFenceSegments(_xmin, _xmax, _ymin, _ymax, _shiftkey)
        self.selectFencePatches(_xmin, _xmax, _ymin, _ymax, _shiftkey)

    # ---------------------------------------------------------------------
    def selectFencePoints(self, _xmin, _xmax, _ymin, _ymax, _shiftkey):
            return False

    # ---------------------------------------------------------------------
    def selectFenceSegments(self, _xmin, _xmax, _ymin, _ymax, _shiftkey):
        if self.model.isEmpty():
            return False

        oneSegmentSelected = False

        # Select segments
        segments = self.model.getSegments()
        for i in range(0, len(segments)):
            xmin_c, xmax_c, ymin_c, ymax_c = segments[i].getBoundBox()
            if((xmin_c < _xmin) or (xmax_c > _xmax) or
               (ymin_c < _ymin) or (ymax_c > _ymax)):
                inFence = False
            else:
                inFence = True

            if inFence:
                # Select segment inside fence
                segments[i].setSelected(True)
                oneSegmentSelected = True
            else:
                if not _shiftkey:
                    segments[i].setSelected(False)

        return oneSegmentSelected

    # ---------------------------------------------------------------------
    def selectFencePatches(self, _xmin, _xmax, _ymin, _ymax, _shiftkey):
        if self.model.isEmpty():
            return False

        onePatchSelected = False

        # Select patches
        patches = self.model.getPatches()
        for i in range(0, len(patches)):
            xmin_c, xmax_c, ymin_c, ymax_c = patches[i].getBoundBox()
            if((xmin_c < _xmin) or (xmax_c > _xmax) or
               (ymin_c < _ymin) or (ymax_c > _ymax)):
                inFence = False
            else:
                inFence = True

            if inFence:
                # Select patch inside fence
                patches[i].setSelected(True)
                onePatchSelected = True
            else:
                if not _shiftkey:
                    patches[i].setSelected(False)

        return onePatchSelected

    # ---------------------------------------------------------------------
    def selectReshapeCurve(self, _x,  _y,  _tol):
        self.model.setCurrTol(_tol)
        if self.model.isEmpty():
            return None
        if self.reshape is None:
            return None

        # Select segment
        id_target = -1
        dmin = _tol
        segments = self.model.getSegments()
        for i in range(0, len(segments)):
            # Compute distance between given point and current
            # segment and update minimum distance
            status, xC, yC, d = segments[i].closestPoint(_x, _y)
            if status:
                if d < dmin:
                    dmin = d
                    id_target = i

        # If no segment was picked, just return a null curve
        if id_target == -1:
            return None

        # Get curve that own picked segment.
        curve = segments[id_target].curve

        # Check to see whether the curve associated to the picked
        # segment can be reshaped. For this, check whether the
        # segment that belong to this curve can be reshaped.
        reshapeSeg = self.getCurveSegment(curve)
        if not reshapeSeg.canReshape():
            return None

        # Unselect all segments in model and select the segment
        # that belong to the picked curve.
        for seg in segments:
            seg.setSelected(False)
        reshapeSeg.setSelected(True)
            
        # Return picked curve
        return curve

    # ---------------------------------------------------------------------
    def pickReshapeCurveCtrlPoint(self, _curve, _x,  _y,  _tol):
        self.model.setCurrTol(_tol)
        if self.model.isEmpty():
            return -1
        if self.reshape is None:
            return -1

        id_target = -1
        pt = Pnt2D(_x, _y)
        dist = _tol
        ctrlPts = _curve.getReshapeCtrlPoints()
        for i in range(0, _curve.getNumberOfReshapeCtrlPoints()):
            if Pnt2D.euclidiandistance(pt, ctrlPts[i]) <= dist:
                id_target = i
        return id_target

    # ---------------------------------------------------------------------
    def delSelectEntities(self):
        self.model.delSelectSegments()
        self.model.delSelectPatches()

    # ---------------------------------------------------------------------

    def joinSegments(self, _tol):
        selected = []
        # Correctly get segments from the model
        all_segments = self.model.getSegments()
        for seg in all_segments:
            if self.isSegmentSelected(seg):
                selected.append(seg)
        
        if len(selected) == 2:
            # Call the model's join method
            self.model.joinSegments(selected[0], selected[1], _tol)

    def getNumSelectedSegments(self):
        count = 0
        # Correctly get segments from the model
        all_segments = self.model.getSegments()
        for seg in all_segments:
            if self.isSegmentSelected(seg):
                count += 1
        return count

    def splitSelectedSegments(self, num_pieces):
        if num_pieces < 2:
            return

        # 1. Get the list of selected segments to be split
        segments_to_split = []
        all_segments = self.model.getSegments()
        for seg in all_segments:
            if self.isSegmentSelected(seg):
                segments_to_split.append(seg)

        if not segments_to_split:
            return

        # 2. Generate all new curves from the segments to be split
        all_new_curves = []
        for seg in segments_to_split:
            curve = seg.getCurve()
            try:
                new_curves = curve.split(num_pieces)
                all_new_curves.extend(new_curves)
            except AttributeError:
                print(f"Warning: The curve of type {type(curve).__name__} does not have a 'split' method.")
                pass
        
        # 3. Unselect everything to have a clean state
        self.unselectAll()

        # 4. Add all the newly created curves to the model
        #    The model is responsible for creating segments from them.
        for new_curve in all_new_curves:
            self.model.addCurve(new_curve)

        # 5. Now, select ONLY the original segments that were split
        for seg in segments_to_split:
            seg.setSelected(True)

        # 6. Delete all selected (i.e., the original) segments at once
        self.model.delSelectSegments()

    # ---------------------------------------------------------------------
    def getBoundBox(self):
        if self.model.isEmpty():
            return 0.0, 10.0, 0.0, 10.0
        segments = self.model.getSegments()
        xmin, xmax, ymin, ymax = segments[0].getBoundBox()
        for i in range(1, len(segments)):
            xmin_c, xmax_c, ymin_c, ymax_c = segments[i].getBoundBox()
            xmin = min(xmin_c, xmin)
            xmax = max(xmax_c, xmax)
            ymin = min(ymin_c, ymin)
            ymax = max(ymax_c, ymax)
        return xmin, xmax, ymin, ymax

    # ---------------------------------------------------------------------
    def snapToSegment(self, _x, _y, _tol):
        self.model.setCurrTol(_tol)
        if self.model.isEmpty():
            return False, _x, _y

        xClst = _x
        yClst = _y
        id_target = -1
        dmin = _tol

        segments = self.model.getSegments()
        for i in range(0, len(segments)):
            status, xC, yC, dist = segments[i].closestPoint(_x, _y)
            if status:
                if dist < dmin:
                    xClst = xC
                    yClst = yC
                    dmin = dist
                    id_target = i

        if id_target < 0:
            return False, xClst, yClst

        # If found a closest point, return its coordinates
        return True, xClst, yClst

    # ---------------------------------------------------------------------
    def snapToPoint(self, _x, _y, _tol):
        self.model.setCurrTol(_tol)
        return False, _x, _y

    # ---------------------------------------------------------------------
    def getColorBackground(self):
        return self.colorBackground

    # ---------------------------------------------------------------------
    def getColorSelection(self):
        return self.colorSelection

    # ---------------------------------------------------------------------
    def getColorPoint(self):
        return self.colorPoint

    # ---------------------------------------------------------------------
    def getColorPointSelection(self):
        return self.colorPointSelection

    # ---------------------------------------------------------------------
    def getColorSegment(self):
        return self.colorSegment

    # ---------------------------------------------------------------------
    def getColorSegmentSelection(self):
        return self.colorSegmentSelection

    # ---------------------------------------------------------------------
    def getColorPatch(self):
        return self.colorPatch

    # ---------------------------------------------------------------------
    def getColorPatchSelection(self):
        return self.colorPatchSelection

    # ---------------------------------------------------------------------
    def getColorCollecting(self):
        return self.colorCollecting

    # ---------------------------------------------------------------------
    def getColorGrid(self):
        return self.colorGrid

    # ---------------------------------------------------------------------
    def getColorSdvPoint(self):
        return self.colorSdvPoint

    # ---------------------------------------------------------------------
    def getColorMesh(self):
        return self.colorMesh
