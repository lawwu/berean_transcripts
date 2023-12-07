import os
import unittest
import wave

from berean_transcripts import transcribe_youtube


class TestEnsureWav16k(unittest.TestCase):
    def setUp(self):
        self.test_file = "test.wav"
        with wave.open(self.test_file, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.writeframes(b'\x00\x00' * 44100 * 10)

    def tearDown(self):
        os.remove(self.test_file)
        if os.path.exists("test_16k.wav"):
            os.remove("test_16k.wav")

    def test_ensure_wav_16k_converts_audio_correctly(self):
        transcribe_youtube.ensure_wav_16k("test")
        self.assertTrue(os.path.exists("test_16k.wav"))
        with wave.open("test_16k.wav", 'r') as f:
            self.assertEqual(f.getframerate(), 16000)

    def test_ensure_wav_16k_handles_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            transcribe_youtube.ensure_wav_16k("nonexistent")

if __name__ == "__main__":
    unittest.main()
