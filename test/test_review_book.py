import os
import shutil
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import chess

import clk
import review_config
from review_book import ReviewBook, ReviewNode


class TestReviewBook(unittest.TestCase):
    def setUp(self):
        review_config.INITIAL_INTERVAL = timedelta(minutes=10)
        review_config.MAX_INTERVAL = timedelta(days=2)
        review_config.INTERVAL_INC_FACTOR = 6

        self.topdir = Path('test/tmp')
        self.repdir = self.topdir / 'repertoire'
        self.revdir = self.topdir / 'review'
        if self.topdir.exists():
            shutil.rmtree(self.topdir)
        os.makedirs(self.revdir)
        shutil.copytree('test/repertoire', self.repdir)

        self.board = chess.Board()
        self.book = None

    def tearDown(self):
        shutil.rmtree(self.topdir)

    def test_review_as_black(self):
        self._start_review(chess.BLACK, '2023-01-01T12:00:00')
        self.assertEqual(self.book.pending_review_count(), 3)
        self._play('e4 e5  Nf3 Nc6  @bottom')
        self.assertEqual(self.book.pending_review_count(), 1)

        self._check_review_node('e4', '2023-01-01T12:10:00', '0+1:00')
        self._check_review_node('e4 e5  Nf3', '2023-01-01T12:10:00', '0+1:00')

        self._start_review(chess.BLACK, '2023-01-01T12:01:00')
        self.assertEqual(self.book.pending_review_count(), 1)
        self._play('d4 d5  @bottom')
        self.assertEqual(self.book.pending_review_count(), 0)

        self._check_review_node('d4', '2023-01-01T12:11:00', '0+1:00')

        self._start_review(chess.BLACK, '2023-01-01T12:02:00')
        self.assertEqual(self.book.pending_review_count(), 0)
        self._play('e4 e5  Nf3 Nc6  @bottom')
        self.assertEqual(self.book.pending_review_count(), 0)

        self._check_review_node('e4', '2023-01-01T13:02:00', '0+1:00')
        self._check_review_node('e4 e5  Nf3', '2023-01-01T13:02:00', '0+1:00')

        self._start_review(chess.BLACK, '2023-01-01T14:00:00')
        self.assertEqual(self.book.pending_review_count(), 3)
        self._play('d4 d5  @bottom')
        self.assertEqual(self.book.pending_review_count(), 2)

        self._check_review_node('d4', '2023-01-01T15:00:00', '0+6:00')

        self._start_review(chess.BLACK, '2023-01-01T14:01:00')
        self.assertEqual(self.book.pending_review_count(), 2)
        self._play('e4 e5  Nf3 Nc6  @bottom')
        self.assertEqual(self.book.pending_review_count(), 0)

        self._check_review_node('e4', '2023-01-01T15:01:00', '0+6:00')
        self._check_review_node('e4 e5  Nf3', '2023-01-01T15:01:00', '0+6:00')

        self._start_review(chess.BLACK, '2023-01-01T16:00:00')
        self.assertEqual(self.book.pending_review_count(), 3)
        self._play('d4 a5  @fail/d5')
        self.assertEqual(self.book.pending_review_count(), 3)

        self._check_review_node('d4', '2023-01-01T16:00:00', '0+0:10')

        self._start_review(chess.BLACK, '2023-01-01T16:01:00')
        self.assertEqual(self.book.pending_review_count(), 3)
        self._play('e4 e5  Nf3 Nc6  @bottom')
        self.assertEqual(self.book.pending_review_count(), 1)

        self._check_review_node('e4', '2023-01-01T22:01:00', '1+12:00')
        self._check_review_node('e4 e5  Nf3', '2023-01-01T22:01:00', '1+12:00')

        self._start_review(chess.BLACK, '2023-01-01T16:02:00')
        self.assertEqual(self.book.pending_review_count(), 1)
        self._play('d4 d5  @bottom')
        self.assertEqual(self.book.pending_review_count(), 0)

        self._check_review_node('d4', '2023-01-01T16:12:00', '0+1:00')

        self._start_review(chess.BLACK, '2023-01-02T08:00:00')
        self.assertEqual(self.book.pending_review_count(), 3)
        self._play('d4 d5  @bottom')
        self.assertEqual(self.book.pending_review_count(), 2)

        self._check_review_node('d4', '2023-01-02T09:00:00', '0+6:00')

        self._start_review(chess.BLACK, '2023-01-02T08:30:00')
        self.assertEqual(self.book.pending_review_count(), 2)
        self._play('e4 e5  Nf3 Nc6  @bottom')
        self.assertEqual(self.book.pending_review_count(), 0)

        self._check_review_node('e4', '2023-01-03T20:30:00', '2+0:00')  # MAX_INTERVAL
        self._check_review_node('e4 e5  Nf3', '2023-01-03T20:30:00', '2+0:00')

        # add a pgn (adding variations to a pgn would have the same result)
        os.rename(self.repdir / 'extra.pgn', self.repdir / 'black' / 'extra.pgn')
        self._start_review(chess.BLACK, '2023-01-02T08:40:00')
        self.assertEqual(self.book.pending_review_count(), 1)
        self._play('c4 Nf6  @bottom')
        self.assertEqual(self.book.pending_review_count(), 0)
        self._check_review_node('c4', '2023-01-02T08:50:00', '0+1:00')

        # remove a pgn
        os.remove(self.repdir / 'black' / 'extra.pgn')
        self._start_review(chess.BLACK, '2023-01-02T08:51:00')
        self.assertEqual(self.book.pending_review_count(), 0)
        self._play('d4')
        self._check_review_node('c4', None, None)
        self.assertTrue((self.topdir / 'review/backup/black.pgn.2023-01-02T08:51:00+00:00').exists())

    def test_review_as_white(self):
        self._start_review(chess.WHITE, '2023-01-01T12:00:00')
        self.assertEqual(self.book.pending_review_count(), 13)
        self._play('e4 e5  Nf3 Nc6  Bc4 Nf6  Ng5 d5  exd5 Nxd5  Nxf7 Kxf7  Qf3+ @bottom')
        self.assertEqual(self.book.pending_review_count(), 7)

        self._start_review(chess.WHITE, '2023-01-01T12:01:00')
        self.assertEqual(self.book.pending_review_count(), 7)
        self._play('e4 e5  Nf3 Nc6  Bc4 Nf6  Ng5 d5  exd5 Na5  Bb5+ @bottom')
        self.assertEqual(self.book.pending_review_count(), 6)

        self._start_review(chess.WHITE, '2023-01-01T12:02:00')
        self.assertEqual(self.book.pending_review_count(), 6)
        self._play('e4 e5  Nf3 Nc6  Bc4 Bc5  b4 Bxb4  c3 Ba5  d4 @bottom')
        self.assertEqual(self.book.pending_review_count(), 3)

        self._start_review(chess.WHITE, '2023-01-01T12:03:00')
        self.assertEqual(self.book.pending_review_count(), 3)
        self._play('e4 e5  Nf3 Nc6  Bc4 Bc5  b4 Nxb4  c3 Nc6@bottom')
        self.assertEqual(self.book.pending_review_count(), 1)

        self._start_review(chess.WHITE, '2023-01-01T12:04:00')
        self.assertEqual(self.book.pending_review_count(), 1)
        self._play('e4 e5  Nf3 Nc6  Bc4 Bc5  b4 Be7  b5 @bottom')
        self.assertEqual(self.book.pending_review_count(), 0)

        self._start_review(chess.WHITE, '2023-01-01T12:05:00')
        self.assertEqual(self.book.pending_review_count(), 0)
        self._play('e4 e5  Nf3 Nc6  Bc4 Nf6  a3 @fail/Ng5')
        self.assertEqual(self.book.pending_review_count(), 1)

        self._check_review_node('e4 e5  Nf3 Nc6  Bc4 Nf6', '2023-01-01T12:05:00', '0+0:10')

        self._start_review(chess.WHITE, '2023-01-01T12:06:00')
        self.assertEqual(self.book.pending_review_count(), 1)
        self._play('a3 @fail/e4')
        self.assertEqual(self.book.pending_review_count(), 1)

    def _start_review(self, color, faketime):
        clk.set_fake_time(datetime.fromisoformat(faketime + '+00:00'))
        name = 'white' if color == chess.WHITE else 'black'
        self.book = ReviewBook(self.revdir / (name + '.pgn'), self.repdir / name, color)
        self.board.reset()

    def _play(self, moves):
        for m in moves.split():
            parts = m.split('@')
            san_move = parts[0]
            tag = parts[1] if len(parts) > 1 else None
            if self.board.turn == self.book.user_color:
                self.assertIsNone(tag)
                self.board.push_san(san_move)
            else:
                move, bottom_reached, correct_move = self.book.next_move(self.board)
                fail = move is None and not bottom_reached
                self.assertEqual(bottom_reached, tag is not None and tag == 'bottom')
                self.assertEqual(fail, tag is not None and tag.startswith('fail/'))
                if san_move:
                    self.assertIsNotNone(move)
                    book_san_move = self.board.san(move)
                    self.assertEqual(san_move, book_san_move)
                    self.board.push_san(san_move)
                else:
                    self.assertIsNone(move)
                if fail:
                    self.assertEqual(correct_move, tag.split('/')[1])

    def _check_review_node(self, moves, isotime, interval):
        b = chess.Board()
        for m in moves.split():
            b.push_san(m)
        node, _ = self.book._find_node(b)

        if isotime is None:
            self.assertIsNone(node)
            return

        self.assertIsNotNone(node)
        rn = ReviewNode(node)

        rt = rn.review_time()
        self.assertIsNotNone(rt)
        self.assertEqual(rt.isoformat(), isotime + '+00:00')

        i = rn.interval()
        self.assertIsNotNone(i)
        hours = int(i.seconds // 3600)
        minutes = int(i.seconds % 3600 // 60)
        ii = f"{i.days:d}+{hours:d}:{minutes:02d}"
        self.assertEqual(ii, interval)
