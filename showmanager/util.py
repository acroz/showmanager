
import functools

@functools.total_ordering
class CompoundScore(object):
    def __init__(self, num_rounds, num_best_rounds=None):
        self.points = [0 for i in range(num_rounds)]
        self.num_best_rounds = num_best_rounds

    def __getitem__(self, index):
        return self.points[index]

    def __setitem__(self, index, value):
        self.points[index] = value

    @property
    def total(self):
        return sum(self.points)

    @property
    def best_rounds(self):
        if self.num_best_rounds is None:
            raise ValueError('number of best rounds to take not set')
        return sum(sorted(self.points, reverse=True)[:self.num_best_rounds])

    @property
    def tie_breaker(self):
        if self.num_best_rounds is None:
            raise ValueError('number of best rounds to take not set')
        return sum(sorted(self.points, reverse=True)[self.num_best_rounds:])

    def __lt__(self, other):
        if other is None:
            return False
        if self.num_best_rounds is None:
            return self.total < other.total
        else:
            if self.best_rounds < other.best_rounds:
                return True
            elif self.best_rounds == other.best_rounds:
                return self.tie_breaker < other.tie_breaker
            else:
                return False

    def __eq__(self, other):
        if other is None:
            return False
        if self.num_best_rounds is None:
            return self.total == other.total
        else:
            if self.best_rounds == other.best_rounds:
                return self.tie_breaker == other.tie_breaker
            else:
                return False

class HTMLTable(object):
    def __init__(self, headers, data):
        self.headers = headers
        self.data = data
    def __html__(self):
        html = '<table class="table table-hover table-bordered">\n'
        html += '<thead>'
        html += '<tr>'
        for cell in self.headers:
            html += '<th>{}</th>'.format(cell)
        html += '</tr>'
        html += '</thead>\n'
        html += '<tbody>\n'
        for row in self.data:
            html += '<tr>'
            for cell in row:
                html += '<td>{}</td>'.format(cell)
            html += '</tr>\n'
        html += '</tbody>\n'
        html += '</table>'
        return html

class PointsTable(object):

    def __init__(self, entries, columns, scoring_rounds=None):
        self.columns = columns
        self.data = {e: CompoundScore(len(columns), scoring_rounds)
                     for e in entries}
        self.scoring_rounds = scoring_rounds
    
    def accumulate(self, entry, column, points):
        index = self.columns.index(column)
        self.data[entry][index] += points

    def header(self):
        header = ['Rank', 'Dog No.', 'Handler', 'Dog', 'HRAJ1']
        header += self.columns 
        if self.scoring_rounds is None:
            header += ['Total']
        else:
            header += ['Best {}'.format(self.scoring_rounds), 'Tie Break']
        return header

    def rows(self):

        # Sort by total points, in descending order
        sorted_data = sorted(self.data.items(), key=lambda p: p[1], reverse=True)

        last_rank = None
        last_points = None

        for i, (entry, points) in enumerate(sorted_data):
            
            # Equal rank for equal points
            if points == last_points:
                rank = last_rank
            else:
                rank = i + 1

            last_points = points
            last_rank = rank

            row = [rank, '-' if entry.number is None else entry.number,
                   entry.handler, entry.dog, entry.hraj1]

            for p in points:
                row.append(p)
            
            if self.scoring_rounds is None:
                row.append(points.total)
            else:
                row += [points.best_rounds, points.tie_breaker]

            yield row

    def __html__(self):
        table = HTMLTable(self.header(), self.rows())
        return table.__html__()
