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
    file = {}
    rope = {}
    filename = None
    for p in sorted(edit_plan, key=_sort_key):
        instruction = p[0]
        begin = p[1][-1]
        assert begin[0] == "file"
        if filename != begin[1]:
            if filename:
                # Flush data
                fd = open(filename+".out", 'w')
                for string in rope:
                    fd.write(string)
                fd.write(file['contents'])
                fd.close()
            filename = begin[1]
            file = {'contents': open(filename).read(),
                    'pos': 0,}
            rope = []
        begin = begin[2]
        assert begin >= file['pos']

        if begin > file['pos']:
            to_copy = begin - file['pos']
            rope.append(file['contents'][:to_copy])
            file['pos'] += to_copy
            file['contents'] = file['contents'][to_copy:]

        if instruction in ("remove", "delete"):
            end   = p[2][-1]
            assert end[0] == 'file'
            assert end[1] == filename
            end   = end[2]
            assert begin < end

            to_skip = end - begin
            file['pos'] += to_skip
            skipped = file['contents'][:to_skip]
            file['contents'] = file['contents'][to_skip:]

        if instruction == "remove":
            rope.extend(["/*metav_delete:", skipped, ":metav_delete*/"])
        elif instruction == "delete":
            pass
        elif instruction == "insert":
            insert = str(p[2])
            rope.extend(["/*metav_generated:*/\n",
                         insert,
                         "\n/*:metav_generated*/"])
        else:
            assert False, "Unknown edit plan instruction, "+repr(instruction)
