from compgeom.pnt2d import Pnt2D
from geometry.segment import Segment
from geometry.curves.curve import Curve
from geometry.curves.polyline import Polyline
from geometry.patch import Patch
from compgeom.compgeom import CompGeom
from appmodel import Segment


class AppModel:

    DIST_TOL = 1e-3  # Tolerance value for checking point proximity

    def __init__(self, _controller=None):
        self.controller = _controller
        self.segments = []
        self.patches = []
        self.currTol = 0.0  # current modeling tolerance

    # ---------------------------------------------------------------------
    def isEmpty(self):
        return self.segments == []

    # ---------------------------------------------------------------------
    def getSegments(self):
        return self.segments

    # ---------------------------------------------------------------------
    def getPatches(self):
        return self.patches
    # ---------------------------------------------------------------------
    def addCurve(self, curve):
        new_segment = Segment(curve)
        # Force the polyline to be generated immediately upon creation.
        # This prevents errors when getBoundBox is called before the first paint.
        new_segment.getPolylinePts() 
        self.segments.append(new_segment)

    # ---------------------------------------------------------------------
    def getSelectSegments(self):
        selectedSegments = []
        for seg in self.segments:
            if seg.isSelected():
                selectedSegments.append(seg)
        return selectedSegments

    # ---------------------------------------------------------------------
    def getSelectPatches(self):
        selectedPatches = []
        for ptch in self.patches:
            if ptch.isSelected():
                selectedPatches.append(ptch)
        return selectedPatches

    # ---------------------------------------------------------------------
    def setCurrTol(self, _tol):
        self.currTol = _tol

    # ---------------------------------------------------------------------
    # Insert new segment (faceted version of curve) in the model.
    # The given owning curve is hooked to the segment.
    def insertCurve(self, _curve, _tol):
        self.currTol = _tol
        seg = Segment(_curve)

        # Check for self intersection segment. If that is the case,
        # subdivide the segment into non self intersecting parts,
        # also spliting the original curve.
        self.subdivideSelfIntersected(seg)

    # ---------------------------------------------------------------------
    def reshapeCurve(self, _curve, _tol):
        self.currTol = _tol
        # Get the segment that belong to this curve.
        # Renerate polyline of this segment
        for seg in self.getSegments():
            if seg.getCurve() == _curve:
                seg.resetEquivPolyline()
                # In case a reshaped segment is used by a patch, delete this patch.
                patchesToDelete = []
                for i in range(0, len(self.patches)):
                    for patchSeg in self.patches[i].getSegments():
                        if patchSeg == seg:
                            patchesToDelete.append(self.patches[i])
                            break
                for ptch in patchesToDelete:
                    self.patches.remove(ptch)
                    del ptch
                break

    # ---------------------------------------------------------------------
    def subdivideSelfIntersected(self, _seg):
        # Get the owning curve and polyline of given segment.
        curve = _seg.curve

        polypts = _seg.getPolylinePts()

        # Find the self intersection points of polyline.
        # The function CompGeom.splitSelfIntersected computes the intersection
        # point coordinates and the polyline parametric values along the polyline.
        # These parametric values range from 0.0 to 1.0 in each polyline and correspond
        # to the ratio between the polyline arc length of the intersection point and
        # the total polyline length.
        # In the sequence, these parametric values will be computed on the owning curve
        # parametric representation of the given segment.
        # The returned overlap list contains flags that indicate that the next segment
        # in intersPts overlaps with another segment in polyline.
        status, intersPts, params, overlap = CompGeom.splitSelfIntersected(polypts)

        if not status:
            # Given segment does not have any self intersection: insert it in the
            # model and return.
            self.segments.append(_seg)
            return

        numIntersPts = len(intersPts)

        # Recompute the intersection points based on parametric description of the curve.
        # The parametric value of the intersection points on curve is also recomputed.
        for i in range(0, numIntersPts):
            status = False
            for j in range(i + 1, numIntersPts):
                if Pnt2D.euclidiandistance(intersPts[i], intersPts[j]) < AppModel.DIST_TOL:
                    status, intersPt, params[i], params[j] = Curve.paramCurvesIntersection(
                                                        curve, curve, params[i], params[j])
                    if status:
                        break
            if status:
                intersPts[i].setX(intersPt.getX())
                intersPts[i].setY(intersPt.getY())
                intersPts[j].setX(intersPt.getX())
                intersPts[j].setY(intersPt.getY())

        # Split original segment at the intersection points.
        splitSegs = _seg.split(params, intersPts)

        # In any case, insert a false flag at the beginning of the overlap list.
        # This is done because either the first intersection point is the initial point,
        # in which case an empty segment is returned by the segment split method
        # above, or the first intersection point is not the beginning of curve, in which
        # case the first split segment does not overlap with the curve itself.
        overlap.insert(0, False)

        # Insert segments resulting from self intersection in model
        for i in range(0, numIntersPts + 1):
            seg = splitSegs[i]
            if (seg != []) and (not overlap[i]):
                self.segments.append(seg)

        # Delete original segment
        del _seg

    # ---------------------------------------------------------------------
    def createPatch(self):
        patchSegIDs = []
        patchSegOrients = []
        selInd = []
        masterID = -1
        numSelSegs = 0

       # Build a list of all selected segments.
        for i in range(0, len(self.segments)):
            seg = self.segments[i]
            if seg.isSelected():
                if masterID == -1:
                    # The master segment of region is the first segment found selected.
                    masterID = i
                else:
                    # Save all selected segments, except the master one in a list.
                    selInd.append(i)
 
        # Check for no segment selected.
        if masterID == -1:
            self.controller.popupMessage('Cannot create patch:\n'
                                         'No segment is selected.')
            return

        # Get number of selected segments.
        numSelSegs = len(selInd) + 1

        # Put the index of the master segment in a list of patch segments.
        # First patch point is the first point of the master segment.
        # Set the orientation of the first selected segment as true.
        # The orientation of segments is used to concatenate segments in a
        # consistent order along the patch boundary.
        patchSegIDs.append(masterID)
        patchSegOrients.append(True)
        fstPt = self.segments[masterID].getPntInit()
        curPt = self.segments[masterID].getPntEnd()

        # Traverse list of selected segments trying to identify a closed and
        # countinous chain of segments just using segments end points.
        while(True):
            foundNextSeg = False
            for it in selInd:
                pt0 = self.segments[it].getPntInit()
                pt1 = self.segments[it].getPntEnd()
                segOrientation = True
                if Pnt2D.euclidiandistance(curPt, pt0) < AppModel.DIST_TOL:
                    curPt = pt1
                    segOrientation = True
                    foundNextSeg = True
                elif Pnt2D.euclidiandistance(curPt, pt1) < AppModel.DIST_TOL:
                    curPt = pt0
                    segOrientation = False
                    foundNextSeg = True

                # If found segment along chain of segments, insert it in
                # patch and remove it from list of selected segments.
                if foundNextSeg:
                    patchSegIDs.append(it)
                    selInd.remove(it)
                    patchSegOrients.append(segOrientation)
                    break

            if not foundNextSeg:
                break

        # Check whether number of selected segments is the same as the
        # number of patch segments.
        # Essentially, this is checking whether all selected segments form
        # a continuous chain.
        if numSelSegs != len(patchSegIDs):
            self.controller.popupMessage('Cannot create patch:\n'
                                         'The selected segments do not form a continuous chain.')
            return

        # Check whether first point is equal to last segment point.
        if Pnt2D.euclidiandistance(fstPt, curPt) < AppModel.DIST_TOL:
            # The selected segments form a polygon: a continuous and closed chain.
            # Collect the patch boundary points from the segment points in a
            # consecutive order, respecting segment orientation with respect to the
            # first (masterID) selected segment:
            # If a segment orientation is the same as the first selected segment,
            # store patch points in the same order of the traversed selected segment.
            # Otherwise, store patch points in the reverse order of the traversed
            # selected segment.
            patchPts = []
            patchSegs = []
            for i in range(0, len(patchSegIDs)):
                patchSegs.append(self.segments[patchSegIDs[i]])
                segPoints = self.segments[patchSegIDs[i]].getPolylinePts()
                if patchSegOrients[i]:
                    for j in range(0, len(segPoints) - 1):
                        patchPts.append(segPoints[j])
                else:
                    for j in range(len(segPoints) - 1, 0, -1):
                        patchPts.append(segPoints[j])

            # Check whether the created closed sequence of points are in a
            # counter-clockwise order.  It that is not the case, revert
            # order of points.
            isCCW = CompGeom.isCounterClockwisePolygon(patchPts)
            if not isCCW:
                patchPtsInverted = []
                for j in range(len(patchPts) - 1, -1, -1):
                    patchPtsInverted.append(patchPts[j])
                patchPts = patchPtsInverted

            # Since patch boundary points are always stored in counter-clockwise
            # order, store in patch a vector of segment orientations to indicate
            # that a segment orientation is in counter-clockwise order (true) or
            # in clockwise (false) order with respect the patch boundary.
            patchSegmentsOrients = []
            if isCCW:
                patchSegmentsOrients = patchSegOrients
            else:
                patchSegsInverted = patchSegs.copy()
                patchSegs.clear()
                patchSegs.append(patchSegsInverted[0])
                if patchSegOrients[0]:
                    patchSegmentsOrients.append(False)
                else:
                    patchSegmentsOrients.append(True)
                for i in range(len(patchSegsInverted) - 1, 0, -1):
                    patchSegs.append(patchSegsInverted[i])
                    if patchSegOrients[i]:
                        patchSegmentsOrients.append(False)
                    else:
                        patchSegmentsOrients.append(True)

            # Create a new patch with the boundary points, boundary segments
            # and boundary segments orientations.
            patch = Patch(patchPts, patchSegs, patchSegmentsOrients)
            self.patches.append(patch)

            # Unselect all selected segments
            for seg in self.getSegments():
                if seg.isSelected():
                    seg.setSelected(False)

        else:
            self.controller.popupMessage('Cannot create patch:\n'
                                         'The selected segments do not close off a region.')

    # ---------------------------------------------------------------------
    def delSelectSegments(self):
        # Build a list of segments to keep and segments to delete.
        segments_to_keep = []
        segments_to_delete = []
        for seg in self.segments:
            if seg.isSelected():
                segments_to_delete.append(seg)
            else:
                segments_to_keep.append(seg)

        if not segments_to_delete:
            return

        # For each segment being deleted, handle associated patches.
        for delSeg in segments_to_delete:
            patches_to_delete_for_seg = []
            for ptch in self.patches:
                for patchSeg in ptch.getSegments():
                    if patchSeg == delSeg:
                        patches_to_delete_for_seg.append(ptch)
                        break
            
            for ptch in patches_to_delete_for_seg:
                if ptch in self.patches:
                    self.patches.remove(ptch)
                del ptch

        # Replace the old segments list with the new one.
        self.segments = segments_to_keep

    # ---------------------------------------------------------------------
    def delSelectPatches(self):
        # Delete all selected patches.
        while True:
            onePatchDeleted = False
            for i in range(0, len(self.patches)):
                if self.patches[i].isSelected():
                    ptch = self.patches[i]
                    self.patches.remove(ptch)
                    del ptch
                    onePatchDeleted = True
                    break
            if not onePatchDeleted:
                break

    # ---------------------------------------------------------------------
    def intersectSelectedSegments(self):
        # Build a list of all selected segments.
        selSegs = []
        for seg in self.segments:
            if seg.isSelected():
                selSegs.append(seg)
        # Check to see whether there are exactly two selected segments.
        if len(selSegs) != 2:
            self.controller.popupMessage('You need to select exactly two segments to intersect')
            return

        # Intercept two selected segments
        self.intersectTwoSegments(selSegs[0], selSegs[1])

    # ---------------------------------------------------------------------
    def intersectTwoSegments(self, _segA, _segB):
        # Get the owning curves and polyline of each given segment.
        curveA = _segA.curve
        curveB = _segB.curve

        polyptsA = _segA.getPolylinePts()
        polyptsB = _segB.getPolylinePts()

        # Attract the endpoints of polyline B to the polyline A and
        # vice-versa (within current tolerance value).
        # This is done because the  intersections of the two segments
        # are found first based on the intersection of the polylines
        # of the two segments.
        polylineA = Polyline(polyptsA)
        status, clstPt, dmin, t, tang = polylineA.closestPoint(polyptsB[0].getX(), polyptsB[0].getY())
        if status:
            if dmin <= self.currTol:
                polyptsB[0].setX(clstPt.getX())
                polyptsB[0].setY(clstPt.getY())
        status, clstPt, dmin, t, tang = polylineA.closestPoint(polyptsB[-1].getX(), polyptsB[-1].getY())
        if status:
            if dmin <= self.currTol:
                polyptsB[-1].setX(clstPt.getX())
                polyptsB[-1].setY(clstPt.getY())
        polylineB = Polyline(polyptsB)
        status, clstPt, dmin, t, tang = polylineB.closestPoint(polyptsA[0].getX(), polyptsA[0].getY())
        if status:
            if dmin <= self.currTol:
                polyptsA[0].setX(clstPt.getX())
                polyptsA[0].setY(clstPt.getY())
        status, clstPt, dmin, t, tang = polylineB.closestPoint(polyptsA[-1].getX(), polyptsA[-1].getY())
        if status:
            if dmin <= self.currTol:
                polyptsA[-1].setX(clstPt.getX())
                polyptsA[-1].setY(clstPt.getY())

        # Perform intersection of the two polylines.
        # The function CompGeom.computePolyPolyIntersection computes the intersection
        # point coordinates and the polyline parametric values along the two segments.
        # These parametric values range from 0.0 to 1.0 in each polyline and correspond
        # to the ratio between the polyline arc length of the intersection point and
        # the total polyline length.
        # The returned intersection points intersPtsA follow the same order of the points
        # in polyptsA. The returned parametric values, parsA and parsB_raw, of the
        # intersection points in polyptsA and polyptsB also follow the same order of the
        # points in polyptsA. In the sequence, these parametric values will be computed
        # on the owning curve parametric representation of each segment.
        # The returned overlapA list contains flags that indicate that the next segment
        # in intersPts overlaps with a segment in polyline B.
        status, intersPtsA, parsA, parsB_raw, overlapA = CompGeom.computePolyPolyIntersection(
                                                               polyptsA, polyptsB)
        if not status:
            return

        numIntersPts = len(intersPtsA)

        # Attract each polyline intersection point to the corresponding curve.
        # This is done to redefine the parametric values of the intersection points on each curve
        # based on the respective parametric description, because they were previously calculated
        # based on the equivalent polylines. Just in case, force init parametric value to be 0.0
        # and end parametric value to be 1.0. 
        for i in range (0, numIntersPts):
            StA, clstPt, dmin, parsA[i], tang = curveA.closestPointParam(
                                                    intersPtsA[i].getX(), intersPtsA[i].getY(), parsA[i])
            if (parsA[i] > -Curve.PARAM_TOL) and (parsA[i] < Curve.PARAM_TOL):
                parsA[i] = 0.0
            if (parsA[i] > 1.0 - Curve.PARAM_TOL) and (parsA[i] < 1.0 + Curve.PARAM_TOL):
                parsA[i] = 1.0

        for i in range (0, numIntersPts):
            StB, clstPt, dmin, parsB_raw[i], tang = curveB.closestPointParam(
                                                    intersPtsA[i].getX(), intersPtsA[i].getY(), parsB_raw[i])
            if (parsB_raw[i] > -Curve.PARAM_TOL) and (parsB_raw[i] < Curve.PARAM_TOL):
                parsB_raw[i] = 0.0
            if (parsB_raw[i] > 1.0 - Curve.PARAM_TOL) and (parsB_raw[i] < 1.0 + Curve.PARAM_TOL):
                parsB_raw[i] = 1.0

        # Recompute the intersection points based on parametric description of curves.
        # The parametric values of the intersection points on each curve are also
        # recomputed.
        intersPts = []
        for i in range(0, numIntersPts):
            status, intersPt, parsA[i], parsB_raw[i] = Curve.paramCurvesIntersection(
                                                    curveA, curveB, parsA[i], parsB_raw[i])
            intersPts.append(intersPt)
        intersPtsA = intersPts

        # Check for reversed order of parametric values of inteserction points along
        # polyline B.
        # If that is the case, reverse the order of lists of parameters and points.
        reversedB = False
        if numIntersPts > 1:
            if parsB_raw[0] > parsB_raw[1]:
                reversedB = True
        parsB = []
        intersPtsB = []
        if reversedB:
            for i in range(numIntersPts - 1, -1, -1):
                par = parsB_raw[i]
                parsB.append(par)
                pt = intersPts[i]
                intersPtsB.append(pt)
        else:
            parsB = parsB_raw
            intersPtsB = intersPts

        # Split both original segments at the intersection points.
        splitSegsA = _segA.split(parsA, intersPtsA)
        splitSegsB = _segB.split(parsB, intersPtsB)

        # In any case, insert a false flag at the beginning of the overlap list of curve A.
        # This is done because either the first intersection point is the initial point of
        # curve A, in which case an empty segment is returned by the segment split method
        # above, or the first intersection point is not the beginning of curve A, in which
        # case the first split segment does not overlap with curve B.
        overlapA.insert(0, False)

        # Insert segments resulting from intersection in model
        for i in range(0, numIntersPts + 1):
            seg = splitSegsA[i]
            if (seg != []) and (not overlapA[i]):
                self.segments.append(seg)
            seg = splitSegsB[i]
            if seg != []:
                self.segments.append(seg)

        # In case an original segment (that will be deleted) is used by a patch,
        # delete this patch.
        patchesToDelete = []
        for i in range(0, len(self.patches)):
            for patchSeg in self.patches[i].getSegments():
                if (patchSeg == _segA) or (patchSeg == _segB):
                    patchesToDelete.append(self.patches[i])
                    break
        for ptch in patchesToDelete:
            self.patches.remove(ptch)
            del ptch

        # Remove original segments
        self.segments.remove(_segA)
        del curveA
        del _segA
        self.segments.remove(_segB)
        del _segB
        del curveB

    # ---------------------------------------------------------------------
    def joinSelectedSegments(self):
        selID1 = -1
        selID2 = -1

       # Build a list of all selected segments.
       # Check to see whether there are exactly two segments and
       # store their IDs.
        for i in range(0, len(self.segments)):
            seg = self.segments[i]
            if seg.isSelected():
                if selID1 == -1:
                    selID1 = i
                elif selID2 == -1:
                    selID2 = i
                else:
                    self.controller.popupMessage('Cannot join segments:\n'
                                                 'Only two segments must be selected.')
                    return
 
        # Check for no segment selected.
        if selID1 == -1:
            self.controller.popupMessage('Cannot join segments:\n'
                                         'No segment is selected.')
            return

        # Check for only one segment selected.
        if selID2 == -1:
            self.controller.popupMessage('Cannot join segments:\n'
                                         'Two segments must be selected.')
            return

        # Get the handles to the two segments selected and the handles to
        # the segments' curves.
        seg1 = self.segments[selID1]
        seg2 = self.segments[selID2]
        crv1 = seg1.getCurve()
        crv2 = seg2.getCurve()

        # Check for closed segment.
        if crv1.isClosed() or crv2.isClosed():
            self.controller.popupMessage('Cannot join segments:\n'
                                         'One segment is a closed loop.')
            return

        # Check to see whether the two segments touch at one common end point.
        # If that is case, get this point.
        seg1PtInit = seg1.getPntInit()
        seg1PtEnd = seg1.getPntEnd()
        seg2PtInit = seg2.getPntInit()
        seg2PtEnd = seg2.getPntEnd()

        if Pnt2D.euclidiandistance(seg1PtInit, seg2PtInit) < AppModel.DIST_TOL:
            ptCommon = seg1PtInit
        elif Pnt2D.euclidiandistance(seg1PtEnd, seg2PtInit) < AppModel.DIST_TOL:
            ptCommon = seg1PtEnd
        elif Pnt2D.euclidiandistance(seg1PtInit, seg2PtEnd) < AppModel.DIST_TOL:
            ptCommon = seg1PtInit
        elif Pnt2D.euclidiandistance(seg1PtEnd, seg2PtEnd) < AppModel.DIST_TOL:
            ptCommon = seg1PtEnd
        else:
            self.controller.popupMessage('Cannot join segments:\n'
                                         'Selected segments do not touch at a common point.')
            return

        # Check whether there is any other segment in the model framing into the
        # common point, in which case do not allow the two segments to be joined.
        for i in range(0, len(self.segments)):
            if (i != selID1) and (i != selID2):
                seg = self.segments[i]
                ptInit = seg.getPntInit()
                ptEnd = seg.getPntEnd()
                if ((Pnt2D.euclidiandistance(ptInit, ptCommon) < AppModel.DIST_TOL) or
                    (Pnt2D.euclidiandistance(ptEnd, ptCommon)  < AppModel.DIST_TOL)):
                    self.controller.popupMessage('Cannot join segments:\n'
                                                 'There is another segment framing into the joining point.')
                    return
 
        # Check whether the two curves may be joined, verifying whether
        # the types of curves are compatible for joining and performing
        # geometric verifications. The new curve resulting from the joining
        # operation is returned.
        status, crvJoined, errorMsg = crv1.join(crv2, ptCommon, AppModel.DIST_TOL)

        # If the two curves could be joined, delete the patches that use the
        # original segments.
        patchesToDelete = []
        for i in range(0, len(self.patches)):
            for patchSeg in self.patches[i].getSegments():
                if (patchSeg == seg1) or (patchSeg == seg2):
                    patchesToDelete.append(self.patches[i])
                    break
        for ptch in patchesToDelete:
            self.patches.remove(ptch)
            del ptch

        # If the two curves could be joined, create a new segment using the resulting
        # joined curve and delete the two original segments.
        # Otherwise, display the returned error message.
        if status == True:
            segJoined = Segment(crvJoined)
            self.segments.append(segJoined)
            self.segments.remove(seg1)
            crv1 = seg1.getCurve()
            del seg1
            del crv1
            self.segments.remove(seg2)
            crv2 = seg2.getCurve()
            del seg2
            del crv2
        else:
            self.controller.popupMessage(errorMsg)
