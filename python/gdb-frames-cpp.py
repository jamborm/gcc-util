# An example originally intended for Suse Labs conference talk, it
# groups backtrace items by classes, IIRC :-) Requires gdb 7.7 or
# later, IIRC :-)

import gdb
import itertools

class ParamTerseBt(gdb.Parameter):
    def __init__(self):
        "Set to on to make backtraces terse"

        super(ParamTerseBt, self).__init__("tersebt", gdb.COMMAND_STACK,
                                           gdb.PARAM_BOOLEAN)
        return

    def get_set_string(self):
        return "Terse backtraces are set to " + str(self.value)
        
    def get_show_string(self, svalue):
        if self.value:
            return "Backtraces set to very tersse"
        return "Backtraces are not terse"
        

terse_bt_param = ParamTerseBt()

class SmallFrameDecorator(gdb.FrameDecorator.FrameDecorator):
    def __init__(self, frame):
        super(SmallFrameDecorator, self).__init__(frame)
        self.frame = frame
        return

    def address(self):
        return None

    def filename(self):
        global terse_bt_param
        if terse_bt_param.value:
            return ""
        return super(SmallFrameDecorator, self).filename().split("/")[-1]

    def line(self):
        global terse_bt_param
        if terse_bt_param.value:
            return None
        return super(SmallFrameDecorator, self).line()

    def frame_args(self):
        global terse_bt_param
        if terse_bt_param.value:
            return None
        return super(SmallFrameDecorator, self).frame_args()


class ElidingFrameDecorator(gdb.FrameDecorator.FrameDecorator):
    def __init__(self, frame, elided_frames):
        super(ElidingFrameDecorator, self).__init__(frame)
        self.frame = frame
        self.elided_frames = elided_frames
        return

    def elided(self):
        return itertools.imap(SmallFrameDecorator, self.elided_frames)

    def address(self):
        return None

    def filename(self):
        global terse_bt_param
        if terse_bt_param.value:
            return None
        l = super(ElidingFrameDecorator, self).filename().split("/")
        if len(l) > 1:
            return l[-2] + "/" + l[-1]
        else:
            return l[0]
        return

    def line(self):
        global terse_bt_param
        if terse_bt_param.value:
            return None
        return super(ElidingFrameDecorator, self).line()

    def frame_args(self):
        global terse_bt_param
        if terse_bt_param.value:
            return None
        return super(ElidingFrameDecorator, self).frame_args()

class ElidingFrameFilter():

    def __init__(self):
        """Create and register the filter"""
 
        self.name = "Foo"
        self.priority = 100
        # Register this frame filter with the global frame_filters
        self.enabled = True
        self.last_name = ""
        self.first = True

        gdb.frame_filters[self.name] = self
        return

    def filter(self, frame_iter):
        try:
            f = next(frame_iter)
        except StopIteration:
            return
        f_name = f.inferior_frame().name();
        try:
            f_prefix = f_name[:f_name.rindex("::")]
        except ValueError:
            f_prefix = ""
            pass
        efs = []

        while True:
            try:
                nf = next(frame_iter)
            except StopIteration:
                yield ElidingFrameDecorator(f, efs)
                return

            n_name = nf.inferior_frame().name();
            try:
                n_prefix = n_name[:n_name.rindex("::")]
            except ValueError:
                n_prefix = ""
                pass

            if (f_prefix != "" and f_prefix == n_prefix):
                efs.append(nf)
            else:
                yield ElidingFrameDecorator(f, efs)
                f = nf
                f_name = n_name
                f_prefix = n_prefix
                efs = []
                pass
            pass
        return

ElidingFrameFilter()
