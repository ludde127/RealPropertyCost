import numpy as np
import matplotlib.pyplot as plt


class Loan:
    def __init__(self, amount, interest_rate, extra_charge,
                 amortization=0.02, min_amortization=1000, keep_cost_flat=False,
                 rise_percent=1.02, direct_income=None, rent_increase=None, years=100):
        self._years = years

        self.rise_percent = rise_percent
        self.minimum_amortization = min_amortization
        self.amount = amount
        self.interest_rate = interest_rate
        self.extra_charge = extra_charge
        self.amortization = amortization
        self.keep_flat = keep_cost_flat
        self.direct_income = direct_income  # for example rent as a landlord
        self.rent_increase = rent_increase

        self.__month_at = 0

        if self.keep_flat:
            assert isinstance(self.keep_flat, (int, float))
            if self.direct_income is not None:
                self.keep_flat += self.direct_income

        self.__amount_left = self.amount
        self.__amortizations = list()
        self.monthly_payments = list()
        self.payed_off_in = None

        self.__calculate()

    def __iter__(self):
        self.__amount_left = self.amount
        self.__amortizations = list()
        self.__stop_iter_next = False
        self.monthly_payments = list()
        self.__month_at = 0
        return self

    def __next__(self):
        if self.__month_at/12 >= self._years:
            raise StopIteration
        amortization = self.amortization / 12 * self.__amount_left
        if amortization < self.minimum_amortization:
            amortization = self.minimum_amortization
        self.__amortizations.append(amortization)
        self.__amount_left -= amortization
        if self.__amount_left < 100 and self.__amount_left != 0 and self.payed_off_in is None:
            extra = self.__amount_left  # betala inte för mycket
            self.__amount_left = 0
            self.payed_off_in = self.__month_at
        else:
            extra = 0

        payment = amortization + self.__amount_left * self.interest_rate / 12 + self.extra_charge + extra  # Payment
        if self.keep_flat and payment < self.keep_flat:
            self.__amount_left += amortization
            amortization += self.keep_flat - payment
            self.__amount_left -= amortization
            payment = amortization + self.__amount_left * self.interest_rate / 12 + self.extra_charge + extra  # Payment

        self.monthly_payments.append(payment)
        self.__month_at += 1
        return payment

    def __calculate(self):
        for _ in self:
            pass
        print(self)

    def plot_gross_monthly(self):
        plt.plot(range(len(self.monthly_payments)), self.monthly_payments)
        plt.show()

    def plot_net_monthly(self):
        plt.plot(range(len(self.monthly_payments)), self.monthly_net)
        plt.show()

    def plot_net(self):
        plt.plot(range(len(self.monthly_payments)), np.cumsum(self.monthly_net))
        plt.show()

    @property
    def monthly_net(self):
        return [cost - inc for cost, inc in zip(self.monthly_payments, self.monthly_earnings)]

    @property
    def monthly_earnings(self):
        return self.__monthly_earnings(True)

    def __monthly_earnings(self, unrealised=True):
        if not unrealised:
            pct = self.rise_percent
            self.rise_percent = 1
        else:
            pct = self.rise_percent
        past = self.amount
        for i in range(len(self.monthly_payments)):
            i = i + 1
            current = self.amount * (self.rise_percent ** (i / 12))
            if self.direct_income is not None and isinstance(self.direct_income, (int, float)):
                if self.rent_increase is None:
                    yield current - past + self.direct_income
                else:
                    yield current - past + self.direct_income * self.rent_increase ** (i / 12)
            else:
                yield current - past
            past = current
        self.rise_percent = pct

    def __str__(self):
        total = sum(self.monthly_payments)
        months = len(self.monthly_payments)
        if self.payed_off_in is not None:
            years = round(self.payed_off_in/12, 1)
        else:
            years = f">{self._years} years (Unknown)"
        extras = round((total/self.amount - 1) * self.amount, 0)
        earned = sum(list(self.monthly_earnings))
        return f"\nTotal cost {total} (pct amortizes {sum(self.__amortizations)/total}), Extra {round(extras, 0)}," \
               f"\nPayed off in {self.payed_off_in} months ({years}), mean monthly cost {total/months}" \
               f"\nTrue cost per month if property price rise by factor of {self.rise_percent} per year is {(total-earned)/months}" \
               f"\nMean monthly cost when property value increase is not accounted" \
               f" for is {(total-sum(self.__monthly_earnings(False)))/months}" \
               f"\nWith total expenses at {total-earned}"
