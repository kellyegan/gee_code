import unittest
from geecode import Sequence


class TestSequence(unittest.TestCase):

    def setUp(self):
        self.s = Sequence()
        self.s.cmd("M73", p=0, r=0, comment="set print progress")
        self.s.cmd("M205", x=10, y=10, z=0.2, e=4.5, comment="sets the jerk limits, mm/sec")
        self.s.cmd("M207", comment="Fans off")

    def test_add_command(self):
        """Add a command to the sequence"""
        s = Sequence()

        s.cmd("G1", x=15, y=16, e=0.05)
        self.assertEqual(len(s._commands), 1)

        # Add second command
        s.cmd("G1", x=25, y=36, e=0.05)
        self.assertEqual(len(s._commands), 2)

    def test_generate_gcode(self):
        """Test if generates correct gcode"""
        expected_output = "M73 P0 R0                          ; set print progress\n" \
                          "M205 X10 Y10 Z0.2 E4.5             ; sets the jerk limits, mm/sec\n" \
                          "M207                               ; Fans off"
        actual_output = "\n".join(self.s.generate())
        self.assertEqual(expected_output, actual_output)

    def test_move_command(self):
        """Should generate a G1 command using move() method"""
        s = Sequence()
        s.move(f=900, comment="Set acceleration")
        s.move(z=0.2, e=0.02)
        s.move(x=20, y=25, e=0.1)
        expected_output = "G1 F900                            ; Set acceleration\n" \
                          "G1 Z0.2 E0.02\n" \
                          "G1 X20 Y25 E0.1"

        actual_output = "\n".join(s.generate())
        self.assertEqual(expected_output, actual_output)

    def test_custom_indent(self):
        """Test if sequence applies a custom comment indentation"""
        expected_output = "M73 P0 R0                ; set print progress\n" \
                          "M205 X10 Y10 Z0.2 E4.5   ; sets the jerk limits, mm/sec\n" \
                          "M207                     ; Fans off"
        actual_output = "\n".join(self.s.generate(indent=25))
        self.assertEqual(expected_output, actual_output)

    def test_no_comment(self):
        """Test if sequence applies a custom comment indentation"""
        expected_output = "M73 P0 R0\n" \
                          "M205 X10 Y10 Z0.2 E4.5\n" \
                          "M207"
        actual_output = "\n".join(self.s.generate(comments=False))
        self.assertEqual(expected_output, actual_output)

    def test_variable(self):
        """Should use a variable that can be set when the sequence generates"""
        sequence = Sequence()
        sequence.cmd("G1", x="$size", y=0, e=0.2)
        sequence.cmd("G1", x="$size", y="$size", e=0.2)
        sequence.cmd("G1", x=0, y="$size", e=0.2)
        sequence.cmd("G1", x=0, y=0, e=0.2)

        expected_output = 'G1 X20 Y0 E0.2\n' \
                          'G1 X20 Y20 E0.2\n' \
                          'G1 X0 Y20 E0.2\n' \
                          'G1 X0 Y0 E0.2'
        actual_output = "\n".join(sequence.generate(size=20))
        self.assertEqual(expected_output, actual_output)

    def test_sub_sequence(self):
        """Test addition of a subsequence to a sequence"""
        main_sequence = Sequence()

        # Creates a subsequence that draws a square on the x,y plane
        sub_sequence = Sequence()
        sub_sequence.cmd("G1", x=10, y=0, e=0.2)
        sub_sequence.cmd("G1", x=10, y=10, e=0.2)
        sub_sequence.cmd("G1", x=0, y=10, e=0.2)
        sub_sequence.cmd("G1", x=0, y=0, e=0.2)

        # Adds the subsequence twice moving the z up between moves
        main_sequence.cmd("G28", comment="Home axes")
        main_sequence.cmd("G1", z=0.2)
        main_sequence.sub(sub_sequence)
        main_sequence.cmd("G1", z=0.4)
        main_sequence.sub(sub_sequence)

        expected_output = "G28                                ; Home axes\n" \
                          "G1 Z0.2\n" \
                          "G1 X10 Y0 E0.2\n" \
                          "G1 X10 Y10 E0.2\n" \
                          "G1 X0 Y10 E0.2\n" \
                          "G1 X0 Y0 E0.2\n" \
                          "G1 Z0.4\n" \
                          "G1 X10 Y0 E0.2\n" \
                          "G1 X10 Y10 E0.2\n" \
                          "G1 X0 Y10 E0.2\n" \
                          "G1 X0 Y0 E0.2"

        actual_output = "\n".join(main_sequence.generate())
        self.assertEqual(expected_output, actual_output)

    def test_sub_sequence_variable(self):
        """Should allow assignment of variables when a subsequence is generated"""
        main_sequence = Sequence()

        # Creates a subsequence that draws a square on the x,y plane
        sub_sequence = Sequence()
        sub_sequence.cmd("G1", x=0, y="$size", e=0.2, comment="Begin square")
        sub_sequence.cmd("G1", x="$size", y="$size", e=0.2)
        sub_sequence.cmd("G1", x="$size", y=0, e=0.2)
        sub_sequence.cmd("G1", x=0, y=0, e=0.2)

        # Adds the subsequence twice moving the z up between moves
        main_sequence.cmd("G28", comment="Home axes")
        main_sequence.cmd("G1", z=0.2)
        main_sequence.sub(sub_sequence, size=30)
        main_sequence.cmd("G1", z=0.4)
        main_sequence.sub(sub_sequence, size=30.4)

        expected_output = "G28                                ; Home axes\n" \
                          "G1 Z0.2\n" \
                          "G1 X0 Y30 E0.2                     ; Begin square\n" \
                          "G1 X30 Y30 E0.2\n" \
                          "G1 X30 Y0 E0.2\n" \
                          "G1 X0 Y0 E0.2\n" \
                          "G1 Z0.4\n" \
                          "G1 X0 Y30.4 E0.2                   ; Begin square\n" \
                          "G1 X30.4 Y30.4 E0.2\n" \
                          "G1 X30.4 Y0 E0.2\n" \
                          "G1 X0 Y0 E0.2"

        actual_output = "\n".join(main_sequence.generate())
        self.assertEqual(expected_output, actual_output)
