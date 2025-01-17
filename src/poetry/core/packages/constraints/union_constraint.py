from typing import TYPE_CHECKING
from typing import Tuple
from typing import Union

from poetry.core.packages.constraints.base_constraint import BaseConstraint
from poetry.core.packages.constraints.constraint import Constraint
from poetry.core.packages.constraints.empty_constraint import EmptyConstraint
from poetry.core.packages.constraints.multi_constraint import MultiConstraint


if TYPE_CHECKING:
    from poetry.core.packages.constraints import ConstraintTypes  # noqa


class UnionConstraint(BaseConstraint):
    def __init__(self, *constraints: Constraint) -> None:
        self._constraints = constraints

    @property
    def constraints(self) -> Tuple[Constraint]:
        return self._constraints

    def allows(
        self, other: Union[Constraint, MultiConstraint, "UnionConstraint"]
    ) -> bool:
        for constraint in self._constraints:
            if constraint.allows(other):
                return True

        return False

    def allows_any(self, other: "ConstraintTypes") -> bool:
        if other.is_empty():
            return False

        if other.is_any():
            return True

        if isinstance(other, Constraint):
            constraints = [other]
        else:
            constraints = other.constraints

        for our_constraint in self._constraints:
            for their_constraint in constraints:
                if our_constraint.allows_any(their_constraint):
                    return True

        return False

    def allows_all(self, other: "ConstraintTypes") -> bool:
        if other.is_any():
            return False

        if other.is_empty():
            return True

        if isinstance(other, Constraint):
            constraints = [other]
        else:
            constraints = other.constraints

        our_constraints = iter(self._constraints)
        their_constraints = iter(constraints)
        our_constraint = next(our_constraints, None)
        their_constraint = next(their_constraints, None)

        while our_constraint and their_constraint:
            if our_constraint.allows_all(their_constraint):
                their_constraint = next(their_constraints, None)
            else:
                our_constraint = next(our_constraints, None)

        return their_constraint is None

    def intersect(self, other: "ConstraintTypes") -> "ConstraintTypes":
        if other.is_any():
            return self

        if other.is_empty():
            return other

        if isinstance(other, Constraint):
            if self.allows(other):
                return other

            return EmptyConstraint()

        new_constraints = []
        for our_constraint in self._constraints:
            for their_constraint in other.constraints:
                intersection = our_constraint.intersect(their_constraint)

                if not intersection.is_empty() and intersection not in new_constraints:
                    new_constraints.append(intersection)

        if not new_constraints:
            return EmptyConstraint()

        return UnionConstraint(*new_constraints)

    def union(self, other: Constraint) -> "UnionConstraint":
        if isinstance(other, Constraint):
            constraints = self._constraints
            if other not in self._constraints:
                constraints += (other,)

            return UnionConstraint(*constraints)

    def __eq__(self, other: "ConstraintTypes") -> bool:

        if not isinstance(other, UnionConstraint):
            return False

        return sorted(
            self._constraints, key=lambda c: (c.operator, c.version)
        ) == sorted(other.constraints, key=lambda c: (c.operator, c.version))

    def __str__(self) -> str:
        constraints = []
        for constraint in self._constraints:
            constraints.append(str(constraint))

        return " || ".join(constraints)
