#
# finish-lldb-python.py
#
# This script modifies the lldb module (which was automatically generated via
# running swig) to support iteration for certain lldb objects, adds a global
# variable 'debugger_unique_id' and initializes it to 0.
#
# It also calls SBDebugger.Initialize() to initialize the lldb debugger
# subsystem.
#

import sys, re, StringIO

if len (sys.argv) != 2:
    output_name = "./lldb.py"
else:
    output_name = sys.argv[1] + "/lldb.py"

# print "output_name is '" + output_name + "'"

#
# lldb_iter() should appear before the our first SB* class definition.
#
lldb_iter_def = '''
# ===================================
# Iterator for lldb container objects
# ===================================
def lldb_iter(obj, getsize, getelem):
    """A generator adaptor to support iteration for lldb container objects."""
    size = getattr(obj, getsize)
    elem = getattr(obj, getelem)
    for i in range(size()):
        yield elem(i)

'''

#
# This supports the iteration protocol.
#
iter_def = "    def __iter__(self): return lldb_iter(self, '%s', '%s')"
module_iter = "    def module_iter(self): return lldb_iter(self, '%s', '%s')"
breakpoint_iter = "    def breakpoint_iter(self): return lldb_iter(self, '%s', '%s')"

#
# The dictionary defines a mapping from classname to (getsize, getelem) tuple.
#
d = { 'SBBreakpoint':  ('GetNumLocations',   'GetLocationAtIndex'),
      'SBCompileUnit': ('GetNumLineEntries', 'GetLineEntryAtIndex'),
      'SBDebugger':    ('GetNumTargets',     'GetTargetAtIndex'),
      'SBModule':      ('GetNumSymbols',     'GetSymbolAtIndex'),
      'SBProcess':     ('GetNumThreads',     'GetThreadAtIndex'),
      'SBThread':      ('GetNumFrames',      'GetFrameAtIndex'),

      'SBInstructionList':   ('GetSize', 'GetInstructionAtIndex'),
      'SBStringList':        ('GetSize', 'GetStringAtIndex',),
      'SBSymbolContextList': ('GetSize', 'GetContextAtIndex'),
      'SBValueList':         ('GetSize',  'GetValueAtIndex'),

      'SBType':  ('GetNumberChildren', 'GetChildAtIndex'),
      'SBValue': ('GetNumChildren',    'GetChildAtIndex'),

      'SBTarget': {'module':     ('GetNumModules', 'GetModuleAtIndex'),
                   'breakpoint': ('GetNumBreakpoints', 'GetBreakpointAtIndex')
                   }
      }

# The new content will have the iteration protocol defined for our lldb objects.
new_content = StringIO.StringIO()

with open(output_name, 'r') as f_in:
    content = f_in.read()

# The pattern for recognizing the beginning of an SB class definition.
class_pattern = re.compile("^class (SB.*)\(_object\):$")

# The pattern for recognizing the beginning of the __init__ method definition.
init_pattern = re.compile("^    def __init__\(self, \*args\):")

# These define the states of our state machine.
NORMAL = 0
DEFINING_ITERATOR = 1
DEFINING_TARGET_ITERATOR = 2

# The lldb_iter_def only needs to be inserted once.
lldb_iter_defined = False;

state = NORMAL
for line in content.splitlines():
    if state == NORMAL:
        match = class_pattern.search(line)
        if not lldb_iter_defined and match:
            print >> new_content, lldb_iter_def
            lldb_iter_defined = True
        if match and match.group(1) in d:
            # Adding support for iteration for the matched SB class.
            cls = match.group(1)
            # Next state will be DEFINING_ITERATOR.
            state = DEFINING_ITERATOR
    elif state == DEFINING_ITERATOR:
        match = init_pattern.search(line)
        if match:
            # We found the beginning of the __init__ method definition.
            # This is a good spot to insert the iteration support.
            #
            # But note that SBTarget has two types of iterations.
            if cls == "SBTarget":
                print >> new_content, module_iter % (d[cls]['module'])
                print >> new_content, breakpoint_iter % (d[cls]['breakpoint'])
            else:
                print >> new_content, iter_def % d[cls]
            # Next state will be NORMAL.
            state = NORMAL

    # Pass the original line of content to the ew_content.
    print >> new_content, line
    
with open(output_name, 'w') as f_out:
    f_out.write(new_content.getvalue())
    f_out.write("debugger_unique_id = 0\n")
    f_out.write("SBDebugger.Initialize()\n")
