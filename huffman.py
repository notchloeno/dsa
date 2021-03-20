"""Implements Huffman Encoding and Decoding for any UNICODE encoded string"""
import os
import time
import logging
from datetime import datetime
import bitarray

logging.basicConfig(level=logging.DEBUG)
clock = 0


class Node:
    def __init__(self, value, char=None, left=None, right=None):
        self.value = value
        self.char = char
        self.left = left
        self.right = right
        return

    def __repr__(self):
        return "Node({}, {})".format(
            self.value,
            self.char
            )

    def get_schema(self, pattern: str = "") -> dict:
        """
        Returns a dictionary mapping characters to a binary string, which is used to Huffman encode them
        :param pattern: Should NOT be parsed - used for recursion
        :return: The encoding dictionary
        """
        left, right = self.left, self.right

        # If this is an end node, return da schema table
        if self.char is not None:
            return {self.char: pattern}

        # Otherwise, recursion time. Append to the pattern :)
        left_schema = left.get_schema(
            pattern="{}0".format(pattern))
        right_schema = right.get_schema(
            pattern="{}1".format(pattern))
        
        return left_schema | right_schema


def generate_frequency_map(string: str) -> dict:
    """Returns a dictionary with characters as keys, and frequency as values
    :param string: The string to generate a frequency map for
    :return: The frequency map
    """
    print("Generating frequency map...")
    char_map = {}
    for char in string:
        if char in char_map.keys():
            char_map[char] += 1
        else:
            char_map[char] = 1
    print("Done.")
    stopwatch()
    return char_map


def construct_tree(char_map: dict) -> Node:
    """
    Generates a Huffman tree from a frequency map
    :param char_map: The frequency map for the string the tree will be generated for
    :return: The top node of the Huffman tree
    """
    ascending_keys = [Node(char_map[k], k) for k in char_map.keys()]
    while len(ascending_keys) > 1:
        # Re-sort the list as it the 'value' of a node changes when children are added
        ascending_keys.sort(key=lambda x: x.value)
        # Pop the first two elements
        left = ascending_keys.pop(0)
        right = ascending_keys.pop(0)
        # Generate a new parent node
        new_parent_node = Node(
            left.value + right.value,
            None,
            left,
            right
            )
        
        ascending_keys.append(new_parent_node)
    
    return ascending_keys[0]


def encode_string_with_schema(string: str, encoding: dict) -> str:
    """
    Encodes a string using a dictionary mapping generated from a Huffman tree
    :param string: The string to be encoded
    :param encoding: The dictionary mapping
    :return: An encoded string of 1s and 0s
    """
    output = []
    for char in string:
        output.append(encoding[char])
    return "".join(output)


def decode_string_with_schema(string: str, encoding: dict) -> str:
    """
    Decodes a string using a dictionary mapping generated from a Huffman tree
    :param string: The string to be decoded
    :param encoding: The dictionary mapping
    :return: A decoded string
    """
    # Swap the encoding dictionary
    encoding = dict((v, k) for k, v in encoding.items())
    output = ""
    pattern = ""
    for char in string:
        pattern += char
        if pattern in encoding:
            output += encoding[pattern]
            pattern = ""
    return output


# Returns the encoding and the string
def huffman_encode(string: str) -> tuple:
    """
    Returns an encoding and an encoded string for the given string
    :param string: The string to encode
    :return: The encoding dictionary, the encoded string, the frequency map of the original string
    """
    freq_map = generate_frequency_map(string)
    print("Generating tree...")
    top_node = construct_tree(freq_map)
    print("Done.")
    stopwatch()
    print("Generating encoding dict...")
    encoding = top_node.get_schema()  # Recursively generates a dict from the tree
    print("Done.")
    stopwatch()
    print("Encoding string...")
    encoded_string = encode_string_with_schema(string, encoding)
    print("Done.")
    stopwatch()
    return encoding, encoded_string, freq_map


def save_to_file(string: str, character_map: dict, file_name: str) -> None:
    """
    Serialises an encoded string and scheme to a file
    :param string: The encoded binary string to be saved to a file
    :param character_map: The frequency map of the *original* string
    :param file_name: The name of the original file
    """

    # Append a null byte as an "end of frequency map" marker
    character_map = repr(character_map)
    bits = bitarray.bitarray("00000000")
    bits.extend(string)

    # Create the file
    open("{}.huff".format(file_name), "w").close()
    # Write to it
    with open("{}.huff".format(file_name), "r+b") as file:
        file.write(character_map.encode("utf-8"))  # Store the frequency map so a tree can be reconstructed later
        bits.tofile(file)


# TODO: Split this function up, too much is going on
def decompress_from_file(file_name: str) -> None:
    """
    Decompresses a file and saves the decoded data to a new file
    :param file_name: The name of the encoded .huff file
    :return: None
    """
    # TODO: Confirm the file exists
    # Here
    #  Whilst this won't stop a determined user, it should hopefully reduce user error
    if not file_name[-5:] == ".huff":
        print("You are attempting to decompress a file without the .huff extension.")
        print("If the file was not compressed using this software you may experience data loss.")
        print("Enter \"Y\" to continue - any other input will cancel the command.")
        if not input("> ").lower() == "y":
            return

    freq_map = None
    bits = bitarray.bitarray()
    with open(file_name, "rb") as compressed_file:
        # Load the binary data into a bitarray object
        bits.fromfile(compressed_file)
        # Loop through bytes until we find our null marker, and then everything before that is the frequency map
        null_marker = bitarray.bitarray("00000000")
        # We're looking for a null byte, so we loop through 8 bits at a time
        byte_count = int(len(bits)/8)
        for i in range(byte_count):
            bit_slice = bits[i*8: i*8 + 8]
            if bit_slice == null_marker:  # We've reached the end of the header
                freq_map = bits[0:i*8]  # Grab the frequency map
                bits = bits[i*8 + 8:]  # Trim the header from the file
                break

        if freq_map is None:
            raise ValueError("File header is corrupted or non-existent")

        freq_map_string = freq_map.tobytes().decode("utf-8")
        freq_map = eval(freq_map_string)
    # Convert bitarray to a string of 1s and 0s. In retrospect this probably should have all been done in lists
    encoded_string = "".join(map(lambda x: "1" if x else "0", bits.tolist()))
    # Construct the tree, generate the encoding, and decompress the string
    top_node = construct_tree(freq_map)
    encoding = top_node.get_schema()
    original_text = decode_string_with_schema(encoded_string, encoding)
    # Save the uncompressed file
    with open(file_name.removesuffix(".huff"), "w") as file:
        file.write(original_text)


# TODO: Update for a verbose mode
def stopwatch():
    t = time.time()
    logging.debug("{}ms since program start".format(t - clock))


print("Started at {}".format(datetime.now()))
clock = time.time()

test_file = "fib41"
with open(test_file) as file:
    print("Reading file...")
    data = file.read()
    stopwatch()
    e, s, m = huffman_encode(data)
    print("Saving to file...")
    save_to_file(s, m, test_file)

print("Finished at {}".format(datetime.now()))
stopwatch()
original_file_size = os.path.getsize(test_file)
compressed_file_size = os.path.getsize("{}.huff".format(test_file))
print("Original file size: {}".format(original_file_size))
print("Compressed file size: {}".format(compressed_file_size))
print("Compression ratio: {}\ni.e. file size multiplied by {}".format(
    original_file_size/compressed_file_size,
    compressed_file_size/original_file_size
))

print("Decompressing the file back!")
clock = time.time()
decompress_from_file("{}.huff".format(test_file))
print("Done")
stopwatch()

