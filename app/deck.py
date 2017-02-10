import re
import numpy as np

outlog = []

import logging

from .card import Card
from .multicard import Multicard

logging_level = logging.INFO
# logging_level = logging.DEBUG

# Set logging level
logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging_level)

log = logging.getLogger()


class Deck(object):

    @property
    def found_all(self):
        return all([card.found for card in self.cards])

    @property
    def any_multicards(self):
        return any([type(card) is Multicard for card in self.cards])

    @property
    def found_all_costs(self):
        return all([card.cost_found for card in self.cards])

    def __init__(self, user=None, user_input=None, card_list=None):
        """
        """
        self.cards = []

        if user_input is not None:

            log.debug("Processing User input:")

            for i, row in enumerate(user_input.splitlines()):

                # Delete newline from string
                row = row.replace(r"\n", "")

                # Get rid of multiple adjoining whitespace.
                row = re.sub(r"\s+", " ", row)

                # Strip leading and trainling whitespace.
                row = row.strip()

                # Check that the row is not a comment
                if len(row) > 0 and not row[0] == '#':

                    log.debug("  {}: {}".format(i, row))

                    # If the first character is not a digit, lets assume the
                    # number of cards is just ommited and should be equal to 1.
                    if not row[0].isdigit():
                        row = '1 x ' + row

                    # Regex explained
                    # (1) ... one or more digits
                    # maybe a whitespace
                    # maybe "x"
                    # whitespace
                    # (2) ... anything but "[", "]" at least once plus anything but "[", "]", or whitespace exactly once
                    # maybe a whitespace
                    # (3) ... maybe "[" plus maybe anything plus maybe "]"
                    #
                    # Therefore a string
                    # 4 x Inspiring Vantage [KLD]
                    # will be split into
                    #   count = '4'
                    #   name = 'Inspiring Vantage'
                    #   edition = '[KLD]'
                    #
                    match = re.match(
                        r"(\d+)\s?x?\s([^\[\]]+[^\[\]\s])\s?(\[?.*\]?)", row)

                    if match:
                        count = int(match.group(1))
                        name = match.group(2)
                        edition = match.group(3).replace("[", "").replace("]", "")

                    else:
                        outlog.append("Error while processing input row {}: {}".format(i, row))
                        continue
                        raise ValueError(
                            "Error while processing input row {}: {}".format(i, row))

                    search_hash = Card.hash_name(name)

                    # There may a problem with a wrong appostrophe character in the
                    # input. Loop over possible variants, break on first successfull
                    # search.
                    name_variants = np.unique([name, name.replace("'", "´")])

                    card = None

                    for name_var in name_variants:

                        log.debug("  seaching for: {}".format(name_var))

                        # Search for the card.
                        result = Card.search(name_var, edition)

                        log.debug("  result: {}".format(result))

                        if result:
                            # If the result is a single row, there is no problem,
                            # instantiate a Card.
                            if len(result) == 1:
                                card = Card(**result[0], count=count, user=user)

                            # If there was more matches (should be only possible if
                            # a card with the same name exist in multiple editios),
                            # instantiate a Multicard. That is basically a list of
                            # Card instances with some special methods.
                            else:
                                card = Multicard(
                                    [Card(**c, count=0, search_hash=search_hash, user=user) for c in result])
                                card.multicard_info = "multiple_cards"

                            # Either way, the card was found, so we can break the
                            # search loop.
                            card.found = True
                            break

                    # If the card was not found yet, search for similar names using
                    # fulltext search.
                    if not card:

                        # Prevent db query errors when card name contained "'".
                        # This is somewhat dirty solution...
                        # name = name.replace("'", "´")

                        similar = Card.search_similar(name, limit=30)

                        if similar:
                            card = Multicard(
                                [Card(**c, count=0, search_hash=search_hash, user=user) for c in similar])
                            card.found = True
                            card.name = name
                            card.multicard_info = "similar_search"

                        else:
                            # If the result is empty, we instantiate an empty Card.
                            card = Card()
                            card.found = False

                    # Store some requested properties.
                    # card.count = count
                    card.name_req = name
                    card.edition_req = edition
                    card.search_hash = search_hash

                    # Append the card to the deck list.
                    self.cards.append(card)

        elif card_list is not None:

            log.debug(card_list)

            for i, c in enumerate(card_list):

                card_id = c['id']
                count = int(c['count'])

                # Search for the card.
                result = Card.search_by_id(card_id)

                if result:
                    # If the result is a single row, there is no problem,
                    # instantiate a Card.
                    if len(result) == 1:
                        card = Card(**result[0], count=count)

                    else:
                        raise

                    card.found = True

                else:
                    raise

                # Store some requested properties.
                card.name_req = card.name
                card.edition_req = card.edition_name
                card.search_hash = card.md5

                # Append the card to the deck list.
                self.cards.append(card)

    def print_price_table(self):
        """
        """

        price = 0
        table = []
        footer = []

        columns = ['name', 'manacost', 'edition', 'count', 'count_input', 'owned', 'price', 'multiprice']
        header_texts = ["Card title", "Manacost", "Edition", "Count", "Count", "Owned", "PPU [CZK]", "Price [CZK]"]
        header_data_field = ["title", "manacost", "edition", "count", "count", "Owned", "price", "multiprice"]
        header_data_sortable = [True, True, True, True, True, True, True, True]
        header_widths = [6, 2, 2, 2, 2, 2, 4, 4]

        header = [(col, {
            'text': text,
            'width': width,
            'data_field': data_field,
            'data_sortable': data_sortable},)
                  for col, text, width, data_field, data_sortable
                  in zip(columns, header_texts, header_widths, header_data_field, header_data_sortable)]

        header = dict(header)

        for card in self.cards:

            details = card.details_table_row()

            table.append(details)

            if type(card) is Card:
                if card.cost:
                    price += card.multiprice

            elif type(card) is Multicard:
                for c in card:
                    det = c.details_table_row()
                    det['multicard'] = 'item'
                    det['multicard_info'] = details['multicard_info']
                    table.append(det)

        success = self.found_all and not self.any_multicards and self.found_all_costs

        if not success:
            footer_text = "Minimum price"
            not_success_reason = []

            if not self.found_all:
                not_success_reason.append("some cards not found")
            if self.any_multicards:
                not_success_reason.append("some cards have duplicates")
            if not self.found_all_costs:
                not_success_reason.append("some prices not found")

            footer_text_2 = u'\u2014' + " "  # u'\u2014' is emdash
            footer_text_2 += " and ".join(not_success_reason)

        else:
            footer_text = "Full price"
            footer_text_2 = ""

        footer.append([footer_text, footer_text_2, str(price)])

        table_data = {
            'header': header,
            'body': table,
            'footer': footer,
            'columns': ['name', 'manacost', 'edition', 'count', 'price', 'multiprice'],
            'success': success}

        return table_data, np.unique(outlog)
