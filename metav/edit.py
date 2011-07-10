# This file is part of metav.

# metav is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# metav is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.

# You should have received a copy of the GNU General Public License
# along with metav.  If not, see <http://www.gnu.org/licenses/>.

"""Code for executing an edit plan"""

def _sort_key(p):
    pos = p[1][-1]
    # return filename, charno
    return pos[1], pos[2]

def execute(edit_plan):
    files = {}
    ropes = {}
    for p in sorted(edit_plan, key=_sort_key):
        instruction = p[0]
        begin = p[1][-1]
        assert begin[0] == "file"
        filename = begin[1]
        begin = begin[2]

        if not filename in files:
            files[filename] = {
                'contents': open(filename).read(),
                'pos': 0,
                }
            ropes[filename] = []
            assert begin >= files[filename]['pos']
        if begin > files[filename]['pos']:
            to_copy = begin - files[filename]['pos']
            ropes[filename].append(files[filename]['contents'][:to_copy])
            files[filename]['pos'] += to_copy
            files[filename]['contents'] = files[filename]['contents'][to_copy:]

        if instruction in ("remove", "delete"):
            end   = p[2][-1]
            assert end[0] == 'file'
            assert end[1] == filename
            end   = end[2]
            assert begin < end

            to_skip = end - begin
            files[filename]['pos'] += to_skip
            skipped = files[filename]['contents'][:to_skip]
            files[filename]['contents'] = files[filename]['contents'][to_skip:]

        if instruction == "remove":
            ropes[filename].extend(["/*metav_delete:", skipped, ":metav_delete*/"])
        elif instruction == "delete":
            pass
        elif instruction == "insert":
            insert = str(p[2])
            ropes[filename].extend(["/*metav_generated:*/\n",
                                    insert,
                                    "\n/*:metav_generated*/"])
        else:
            assert False, "Unknown edit plan instruction, "+repr(instruction)

    for filename in ropes:
        fd = open(filename+".out", 'w')
        for string in ropes[filename]:
            fd.write(string)
        fd.write(files[filename]['contents'])
        fd.close()
