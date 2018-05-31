from fuzzywuzzy import process
import blessed

class Selector:

    # The currently selected result
    selected_result = 0

    def __init__(self):
        pass


    def select_item(self,items,num_results=15,title="Select: "):
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
        self.start_location = ( row + -1*(num_results+3)  , col )

        query = ""

        self.update_search_query(term,title,query)
        sorted_results = self.update_results(term,items,num_results,query)

        # Move the cursor to the start (after the query text)
        print(term.move(self.start_location[0],len(title+query))+"",end='',flush=True)

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
                    self.selected_result = 0

                if key == "KEY_ENTER":
                    print(term.clear_eos()+"")
                    return (sorted_results[self.selected_result],sorted_results)

                if key == "KEY_ESCAPE":
                    print(term.clear_eos()+"")
                    return None

                if key == "KEY_DELETE":
                    query = query[:-1]

                # Move up/down the list?
                if key == "KEY_UP":
                    self.update_selected_result(True,num_results)
                if key == "KEY_DOWN":
                    self.update_selected_result(False,num_results)

                # Update the cursory position, query results, and query text
                print(term.move(self.start_location[0],len(title+query)),end='',flush=True)
                self.update_search_query(term,title,query)
                sorted_results = self.update_results(term,sorted_results,num_results,query)

    def update_selected_result(self,direction_up,max_results):

        increment_by = -1 if direction_up else 1

        self.selected_result += increment_by
        #print(self.selected_result)
        #blessed.Terminal().inkey()

        if self.selected_result >= max_results:
            self.selected_result = 0
        elif self.selected_result < 0:
            self.selected_result = max_results - 1

    def update_search_query(self,term,title,query=""):
        # Have to do -3 here since the rows start at 1, and because we're appending a whitespace
        with term.location(x=0,y=self.start_location[0]):
            print(term.clear_eol() + title + query, end='')

    def update_results(self,term,results,num_results,query=""):

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
            

        selected = self.selected_result
        result_number = 0

        # Print the results
        with term.location(x=0,y=self.start_location[0]+2):
            for result in results[:max_index-1]:
                term.clear_eol()
                # Print the selected result as colorized
                if result_number == selected:
                    print( term.black_on_white(term.clear_eol()+result), end='',flush=True )
                    # Clear the remaining background color after the line is finished printing
                    print( term.clear_eol() + '')
                else:
                    print(term.clear_eol()+result)

                result_number += 1

            # Print the LAST item of the list without the trailing newline, important to preserve our UI
            term.clear_eol()
            if result_number == selected:
                print(term.black_on_white(term.clear_eol+results[max_index-1]), end='')
                print( term.clear_eol() + '', end='')
            else:
                print(term.clear_eol+results[max_index-1], end='')

        # Update the global sorted list
        return results.copy()


    def results_to_show(self):
        return min(self.NUM_RESULTS, len(self.results))
