# Trace filtering for python, cutting off things that are rarely
# interesting.  I believe this requires gdb 7.7 or later.  I will
# incorporate this to gdbbasic.py soon.

import gdb
import itertools

class MinimalFrameDecorator(gdb.FrameDecorator.FrameDecorator):
    def __init__(self, frame):
        super(MinimalFrameDecorator, self).__init__(frame)
        self.frame = frame
        return

    def address(self):
        return None

    def filename(self):
        return super(MinimalFrameDecorator, self).filename().split("/")[-1]

    def frame_args(self):
        return None

class ElidingFrameDecorator(gdb.FrameDecorator.FrameDecorator):
    def __init__(self, frame, elided_frames):
        super(ElidingFrameDecorator, self).__init__(frame)
        self.frame = frame
        self.elided_frames = elided_frames
        return

    def elided(self):
        return itertools.imap(MinimalFrameDecorator, self.elided_frames)

    def address(self):
        return None

    def filename(self):
        l = super(ElidingFrameDecorator, self).filename().split("/")
        if len(l) > 1:
            return l[-2] + "/" + l[-1]
        else:
            return l[0]
        return

class ElidingFrameFilter():

    def __init__(self):
        """Create and register the filter"""
 
        self.name = "elided"
        self.priority = 90
        # Register this frame filter with the global frame_filters
        self.enabled = False
        gdb.frame_filters[self.name] = self
        return

    def filter(self, frame_iter):
        for f in frame_iter:
            if f.inferior_frame().name() != "execute_one_pass":   
                yield ElidingFrameDecorator(f, [])
                continue

            efs = []
            while True:
                try:
                    nf = next(frame_iter)
                    if nf.inferior_frame().name() == "toplev_main":
                        break;
                    efs.append(nf)
                except StopIteration:
                    break
                pass
            yield ElidingFrameDecorator(f, efs)
            return
        return


class FrameFilter():

    def __init__(self):
        """Create and register the filter"""
 
        self.name = "shorten"
        self.priority = 100
        # Register this frame filter with the global frame_filters
        self.enabled = True
        gdb.frame_filters[self.name] = self
        return

    def filter(self, frame_iter):
        for f in frame_iter:
            yield ElidingFrameDecorator (f, [])
            if f.inferior_frame().name() == "execute_one_pass":
                return
            pass
        return


FrameFilter()
ElidingFrameFilter()
