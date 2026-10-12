"""Money math for Broke Ben scripts: every number said or shown on screen comes from here.

Usage (prints a short table plus the assumptions line to paste in the description):
  python money_math.py invest  --monthly 200 --rate 0.07 --years 40 [--start 0] [--compounding monthly|yearly]
  python money_math.py loan    --amount 30000 --rate 0.079 --years 6
  python money_math.py card    --balance 5000 --apr 0.24 --payment 150
  python money_math.py inflation --amount 100 --rate 0.03 --years 20
  python money_math.py budget  --income 3000 --spend "Rent=1450,Car=489,Food=312"
"""
import argparse


def invest(monthly, rate, years, start=0.0, compounding='monthly'):
    """Deposits at the end of each month. Returns yearly rows (year, contributed, balance)."""
    rows, bal, put = [], float(start), float(start)
    for y in range(1, years + 1):
        if compounding == 'monthly':
            for _ in range(12):
                bal = bal * (1 + rate / 12) + monthly
                put += monthly
        else:
            bal = (bal + monthly * 12) * (1 + rate)     # yearly deposit, compounded once a year
            put += monthly * 12
        rows.append((y, put, bal))
    return rows


def loan(amount, rate, years):
    """Fixed-rate amortised loan. Returns (monthly payment, total paid, total interest)."""
    n, r = years * 12, rate / 12
    pay = amount / n if r == 0 else amount * r / (1 - (1 + r) ** -n)
    return pay, pay * n, pay * n - amount


def card(balance, apr, payment):
    """Credit card paid with a fixed monthly payment. Returns (months, total interest) or None if it never ends."""
    r, months, interest = apr / 12, 0, 0.0
    while balance > 0.005:
        i = balance * r
        if payment <= i:
            return None
        interest += i
        balance = balance + i - payment
        months += 1
        if months > 1200:
            return None
    return months, interest


def inflation(amount, rate, years):
    """What `amount` today buys after `years` of inflation (in today's dollars)."""
    return amount / (1 + rate) ** years


def money(v):
    return f'${v:,.0f}'


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('invest')
    a.add_argument('--monthly', type=float, required=True)
    a.add_argument('--rate', type=float, required=True)
    a.add_argument('--years', type=int, required=True)
    a.add_argument('--start', type=float, default=0)
    a.add_argument('--compounding', choices=['monthly', 'yearly'], default='monthly')
    b = sub.add_parser('loan')
    b.add_argument('--amount', type=float, required=True)
    b.add_argument('--rate', type=float, required=True)
    b.add_argument('--years', type=int, required=True)
    c = sub.add_parser('card')
    c.add_argument('--balance', type=float, required=True)
    c.add_argument('--apr', type=float, required=True)
    c.add_argument('--payment', type=float, required=True)
    d = sub.add_parser('inflation')
    d.add_argument('--amount', type=float, required=True)
    d.add_argument('--rate', type=float, required=True)
    d.add_argument('--years', type=int, required=True)
    e = sub.add_parser('budget')
    e.add_argument('--income', type=float, required=True)
    e.add_argument('--spend', required=True, help='"Rent=1450,Car=489"')
    x = ap.parse_args()

    if x.cmd == 'invest':
        rows = invest(x.monthly, x.rate, x.years, x.start, x.compounding)
        step = 5 if x.years > 10 else 1
        print(f'{"year":>4} {"put in":>12} {"balance":>12} {"interest":>12}')
        for y, put, bal in rows:
            if y % step == 0 or y == x.years:
                print(f'{y:>4} {money(put):>12} {money(bal):>12} {money(bal - put):>12}')
        timing = 'deposits at the end of each month' if x.compounding == 'monthly' else \
            'the year\'s deposits added at the start of each year'
        print(f'Assumptions: {money(x.monthly)}/month, {x.rate:.1%} average yearly return, '
              f'compounded {x.compounding}, {timing}, starting balance {money(x.start)}.')
    elif x.cmd == 'loan':
        pay, total, interest = loan(x.amount, x.rate, x.years)
        print(f'Monthly payment {money(pay)} | total paid {money(total)} | interest {money(interest)}')
        print(f'Assumptions: {money(x.amount)} at {x.rate:.2%} APR, {x.years} years, fixed monthly payments.')
    elif x.cmd == 'card':
        res = card(x.balance, x.apr, x.payment)
        if res is None:
            print('Never paid off: the payment does not cover the monthly interest.')
        else:
            m, i = res
            print(f'Paid off in {m} months ({m / 12:.1f} years) | interest {money(i)}')
        print(f'Assumptions: {money(x.balance)} balance, {x.apr:.0%} APR, {money(x.payment)}/month, no new spending.')
    elif x.cmd == 'inflation':
        v = inflation(x.amount, x.rate, x.years)
        print(f'{money(x.amount)} in {x.years} years buys what {money(v)} buys today')
        print(f'Assumptions: {x.rate:.1%} yearly inflation.')
    else:
        items = [(k.strip(), float(v)) for k, v in (p.split('=') for p in x.spend.split(','))]
        left = x.income
        print(f'{"Income":<24}{money(x.income):>10}')
        for k, v in items:
            left -= v
            print(f'{k:<24}{"-" + money(v):>10}')
        print(f'{"LEFT OVER":<24}{money(left):>10}')


if __name__ == '__main__':
    main()
