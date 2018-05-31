from fuzzywuzzy import process
import blessed
import operator

class Selector:

    @classmethod
    def select_item(selector,items,num_results=15,title="Query: "):
        """Prompt the user to interactively select an item from a pre-given list of items.
        :param items: The full list of items the user may select from
        :param num_results: The amount of items to show on screen/search for
        :param title: (Optional) The title of the query text input field. Defaults to 'Query:'

        :type items: list
        :type num_results: int
        :type title: string

        :rtype: string
        :return: The selected item, or None if the user canceled
        """
        #I FEEL BLESSED
        term = blessed.Terminal()

        num_results = min(len(items),num_results)

        #start_row, start_col = term.get_location()
        #print("Row: {0}, Col: {0}".format(start_row,start_col))

        # Space out the terminal (important)
        for i in range(num_results +2):
            print("")

        # Where to start drawing our cursor
        row, col = term.get_location() 
        start_location = ( row + -1*(num_results+3)  , col )

        query = ""
        selected_result = 0

        selector.update_search_query(term,start_location,title,query)
        sorted_results = selector.update_results(term,start_location,items,num_results,query,selected_result)

        # Move the cursor to the start (after the query text)
        print(term.move(start_location[0],len(title+query))+"",end='',flush=True)

        while True:
            with term.cbreak():
                key = term.inkey()
                if key.is_sequence:
                    # Are we a special like KEY_UP?
                    key = key.name
                else:
                    # ...or just a normal letter?
                    query += key
                    # Lets reset our selected result, too
                    selected_result = 0

                if key == "KEY_ENTER":
                    print(term.clear_eos()+"")
                    return (sorted_results[selected_result],sorted_results)

                if key == "KEY_ESCAPE":
                    print(term.clear_eos()+"")
                    return None

                if key == "KEY_DELETE":
                    query = query[:-1]

                # Move up/down the list?
                if key == "KEY_UP":
                    selected_result = selector.clamp(selected_result - 1, 0, len(items))
                if key == "KEY_DOWN":
                    selected_result = selector.clamp(selected_result + 1, 0, len(items))

                # Update the cursory position, query results, and query text
                print(term.move(start_location[0],len(title+query)),end='',flush=True)
                selector.update_search_query(term,start_location,title,query)
                sorted_results = selector.update_results(term,start_location,items,num_results,query,selected_result)

    @staticmethod
    def clamp(n, smallest, largest): return max(smallest, min(n, largest))

    @staticmethod
    def update_search_query(term,start_location,title,query=""):
        # Have to do -3 here since the rows start at 1, and because we're appending a whitespace
        with term.location(x=0,y=start_location[0]):
            print(term.clear_eol() + title + query, end='')

    @staticmethod
    def update_results(term,start_location,results,num_results,query="",selected_result=-1):

        num_results = min(len(results),num_results)

        max_index = -1 if num_results > len(results) else num_results

        if len(query) > 0:
            # Perform the sort
            scored_results = process.extract(query,results,limit=len(results) )
            #print(scored_results)
            #term.inkey()

            # Sort the results!
            scored_results = sorted(scored_results, key=operator.itemgetter(1), reverse=True)
            # Copy the first part of the tuple into results (scored_results is in [(value,score),(...)] form
            results = [ result[0] for result in scored_results ]
            

        selected = selected_result
        result_number = 0

        # Print the results
        with term.location(x=0,y=start_location[0]+2):
            for result in results[:max_index-1]:
                term.clear_eol()
                # Print the selected result as colorized
                if result_number == selected:
                    print( term.black_on_white(term.clear_eol()+str(result)), end='',flush=True )
                    # Clear the remaining background color after the line is finished printing
                    print( term.clear_eol() + '')
                else:
                    print(term.clear_eol()+str(result))

                result_number += 1

            # Print the LAST item of the list without the trailing newline, important to preserve our UI
            term.clear_eol()
            if result_number == selected:
                print(term.black_on_white(term.clear_eol+str(results[max_index-1])), end='')
                print( term.clear_eol() + '', end='')
            else:
                print(term.clear_eol+str(results[max_index-1]), end='')

        # Update the global sorted list
        return results.copy()
