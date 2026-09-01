class SupervisorAgent:

    def resolve(self, actions):

        actions = [a for a in actions if a is not None]

        if not actions:
            return None

        # Sort by priority
        actions = sorted(actions, key=lambda x: x["priority"])

        return actions   # return ALL instead of 1