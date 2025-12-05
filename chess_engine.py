# chess_engine.py
# Core chess engine: board, moves, rules (no graphics)

class Square:
    def __init__(self, x, y, piece=None):
        self.x = x
        self.y = y
        self.piece = piece


class Piece:
    def __init__(self, color, name):
        self.color = color
        self.name = name

    def get_moves(self, board, square, state):
        moves = []
        x, y = square.x, square.y
        color = self.color
        opp = "Black" if color == "White" else "White"

        # Pawn
        if self.name == "Pawn":
            d = 1 if color == "White" else -1
            start_y = 1 if color == "White" else 6

            # Forward
            if 0 <= y + d < 8 and board.squares[x][y + d].piece is None:
                moves.append(board.squares[x][y + d])
                if y == start_y and board.squares[x][y + 2 * d].piece is None:
                    moves.append(board.squares[x][y + 2 * d])

            # Captures
            for dx in (-1, 1):
                nx = x + dx
                ny = y + d
                if 0 <= nx < 8 and 0 <= ny < 8:
                    t = board.squares[nx][ny]
                    if t.piece and t.piece.color == opp:
                        moves.append(t)

            # En passant
            if state.en_passant_target:
                ep = state.en_passant_target
                if abs(ep.x - x) == 1 and ep.y == y + d:
                    moves.append(ep)

        # Knight
        elif self.name == "Knight":
            for dx, dy in [(1,2),(1,-2),(-1,2),(-1,-2),(2,1),(2,-1),(-2,1),(-2,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    t = board.squares[nx][ny]
                    if not t.piece or t.piece.color == opp:
                        moves.append(t)

        # Bishop
        elif self.name == "Bishop":
            for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                nx, ny = x + dx, y + dy
                while 0 <= nx < 8 and 0 <= ny < 8:
                    t = board.squares[nx][ny]
                    if not t.piece:
                        moves.append(t)
                    else:
                        if t.piece.color == opp:
                            moves.append(t)
                        break
                    nx += dx
                    ny += dy

        # Rook
        elif self.name == "Rook":
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x + dx, y + dy
                while 0 <= nx < 8 and 0 <= ny < 8:
                    t = board.squares[nx][ny]
                    if not t.piece:
                        moves.append(t)
                    else:
                        if t.piece.color == opp:
                            moves.append(t)
                        break
                    nx += dx
                    ny += dy

        # Queen
        elif self.name == "Queen":
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                nx, ny = x + dx, y + dy
                while 0 <= nx < 8 and 0 <= ny < 8:
                    t = board.squares[nx][ny]
                    if not t.piece:
                        moves.append(t)
                    else:
                        if t.piece.color == opp:
                            moves.append(t)
                        break
                    nx += dx
                    ny += dy

        # King
        elif self.name == "King":
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    t = board.squares[nx][ny]
                    if not t.piece or t.piece.color == opp:
                        moves.append(t)

            # Castling
            y_home = 0 if color == "White" else 7
            if y == y_home and x == 4:
                # King-side
                if state.castling_rights[color]["K"]:
                    if (board.squares[5][y].piece is None and
                        board.squares[6][y].piece is None):
                        rook = board.squares[7][y]
                        if rook.piece and rook.piece.color == color and rook.piece.name == "Rook":
                            moves.append(board.squares[6][y])

                # Queen-side
                if state.castling_rights[color]["Q"]:
                    if (board.squares[1][y].piece is None and
                        board.squares[2][y].piece is None and
                        board.squares[3][y].piece is None):
                        rook = board.squares[0][y]
                        if rook.piece and rook.piece.color == color and rook.piece.name == "Rook":
                            moves.append(board.squares[2][y])

        return moves


class Board:
    def __init__(self):
        self.squares = [[Square(x,y) for y in range(8)] for x in range(8)]

    def setup_pieces(self):
        # White pieces
        order = ["Rook","Knight","Bishop","Queen","King","Bishop","Knight","Rook"]
        for i, name in enumerate(order):
            self.squares[i][0].piece = Piece("White", name)
        for i in range(8):
            self.squares[i][1].piece = Piece("White","Pawn")

        # Black pieces
        for i, name in enumerate(order):
            self.squares[i][7].piece = Piece("Black", name)
        for i in range(8):
            self.squares[i][6].piece = Piece("Black","Pawn")

    def move_piece(self, move):
        f = self.squares[move.from_x][move.from_y]
        t = self.squares[move.to_x][move.to_y]
        piece = f.piece
        f.piece = None

        # En passant capture
        if move.captured and t.piece is None and piece.name == "Pawn":
            cy = move.from_y
            cx = move.to_x
            self.squares[cx][cy].piece = None
        else:
            t.piece = None

        # Place moved piece
        t.piece = piece

        # Promotion
        if move.promotion:
            t.piece = Piece(piece.color, move.promotion)

        # Castling
        if piece.name == "King" and abs(move.to_x - move.from_x) == 2:
            y = move.from_y
            # King-side
            if move.to_x == 6:
                rook_from = self.squares[7][y]
                rook_to = self.squares[5][y]
            else:
                rook_from = self.squares[0][y]
                rook_to = self.squares[3][y]
            rook_to.piece = rook_from.piece
            rook_from.piece = None

    def clone(self):
        b = Board()
        for x in range(8):
            for y in range(8):
                p = self.squares[x][y].piece
                if p:
                    b.squares[x][y].piece = Piece(p.color, p.name)
        return b


class Move:
    def __init__(self, fx, fy, tx, ty, captured=None, promotion=None):
        self.from_x = fx
        self.from_y = fy
        self.to_x = tx
        self.to_y = ty
        self.captured = captured
        self.promotion = promotion

    def __eq__(self, other):
        return (
            isinstance(other, Move) and
            self.from_x == other.from_x and
            self.from_y == other.from_y and
            self.to_x == other.to_x and
            self.to_y == other.to_y and
            self.promotion == other.promotion
        )

    def __hash__(self):
        return hash((self.from_x, self.from_y, self.to_x, self.to_y, self.promotion))


class GameState:
    def __init__(self):
        self.turn = "White"
        self.castling_rights = {
            "White": {"K": True, "Q": True},
            "Black": {"K": True, "Q": True}
        }
        self.en_passant_target = None

    def switch_turn(self):
        self.turn = "Black" if self.turn == "White" else "White"


class MoveGenerator:
    def generate_moves(self, board, color, state):
        moves = []
        for x in range(8):
            for y in range(8):
                sq = board.squares[x][y]
                p = sq.piece
                if p and p.color == color:
                    tgs = p.get_moves(board, sq, state)
                    for t in tgs:
                        captured = t.piece
                        # En passant adjust
                        if p.name == "Pawn" and state.en_passant_target == t:
                            captured = board.squares[t.x][y].piece

                        # Promotion
                        if p.name == "Pawn" and t.y in (7,0):
                            for prom in ["Queen","Rook","Bishop","Knight"]:
                                moves.append(Move(x,y,t.x,t.y,captured,prom))
                        else:
                            moves.append(Move(x,y,t.x,t.y,captured,None))
        return moves


class MoveValidator:
    def is_in_check(self, board, color, state):
        # find king
        kx = ky = None
        for x in range(8):
            for y in range(8):
                p = board.squares[x][y].piece
                if p and p.color == color and p.name == "King":
                    kx, ky = x, y
                    break

        opp = "Black" if color == "White" else "White"
        gen = MoveGenerator()
        opp_moves = gen.generate_moves(board, opp, state)

        for m in opp_moves:
            if m.to_x == kx and m.to_y == ky:
                return True
        return False

    def is_legal(self, board, move, color, state):
        p = board.squares[move.from_x][move.from_y].piece
        if not p or p.color != color:
            return False

        b2 = board.clone()
        b2.move_piece(move)

        # cannot leave king in check
        if self.is_in_check(b2, color, state):
            return False

        # castling check
        if p.name == "King" and abs(move.to_x - move.from_x) == 2:
            # cannot castle from check
            if self.is_in_check(board, color, state):
                return False
            # cannot pass through check
            mid_x = 5 if move.to_x > move.from_x else 3
            b3 = board.clone()
            b3.move_piece(Move(move.from_x, move.from_y, mid_x, move.from_y))
            if self.is_in_check(b3, color, state):
                return False

        return True


class History:
    def __init__(self):
        self.moves = []
        self.positions = {}

    def record_move(self, move, board, state):
        self.moves.append(move)
        key = self.get_position_key(board, state)
        self.positions[key] = self.positions.get(key, 0) + 1

    def get_position_key(self, board, state):
        rows = []
        for y in range(7, -1, -1):
            row = ""
            for x in range(8):
                p = board.squares[x][y].piece
                if not p:
                    row += "."
                else:
                    c = p.name[0]
                    row += c.lower() if p.color == "Black" else c.upper()
            rows.append(row)

        key = "/".join(rows)
        key += " " + state.turn[0]
        return key


class Game:
    def __init__(self):
        self.board = Board()
        self.state = GameState()
        self.history = History()
        self.gen = MoveGenerator()
        self.val = MoveValidator()

        self.game_over = False
        self.game_over_reason = ""
        self.winner = None

    def start_game(self):
        self.board.setup_pieces()

    def get_legal_moves_for_current_player(self):
        color = self.state.turn
        pseudo = self.gen.generate_moves(self.board, color, self.state)
        return [m for m in pseudo if self.val.is_legal(self.board, m, color, self.state)]

    def make_move(self, move):
        if self.game_over:
            return False

        color = self.state.turn
        opp = "Black" if color == "White" else "White"

        if move not in self.get_legal_moves_for_current_player():
            return False

        p = self.board.squares[move.from_x][move.from_y].piece

        # Apply move
        self.board.move_piece(move)

        # Update castling rights
        if p.name == "King":
            self.state.castling_rights[color]["K"] = False
            self.state.castling_rights[color]["Q"] = False

        if p.name == "Rook":
            home_y = 0 if color == "White" else 7
            if move.from_y == home_y:
                if move.from_x == 0:
                    self.state.castling_rights[color]["Q"] = False
                elif move.from_x == 7:
                    self.state.castling_rights[color]["K"] = False

        # EP target reset
        self.state.en_passant_target = None
        if p.name == "Pawn" and abs(move.to_y - move.from_y) == 2:
            mid = (move.from_y + move.to_y)//2
            self.state.en_passant_target = self.board.squares[move.from_x][mid]

        self.history.record_move(move, self.board, self.state)

        self.state.switch_turn()
        
        self._check_end()
        return True

    def _check_end(self):
        moves = self.get_legal_moves_for_current_player()
        color = self.state.turn

        # No legal moves
        if not moves:
            if self.val.is_in_check(self.board, color, self.state):
                self.game_over = True
                opp = "Black" if color == "White" else "White"
                self.winner = opp
                self.game_over_reason = f"{opp} wins by checkmate"
            else:
                self.game_over = True
                self.winner = None
                self.game_over_reason = "Stalemate"
