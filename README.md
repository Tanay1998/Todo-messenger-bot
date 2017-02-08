
Features Supported: 
1. Add a new task
2. Mark a task as finished
3. Delete tasks 
4. List all tasks to do 
5. List all complete tasks 
6. Basic NLP for flexible queries (support for usage of multiple verbs, and much more flexible query format)
7. Searching for todo items
8. Clear all todos (User can select if they want to delete all completed items, all incomplete items, or all elements)
9. Displays a tutorial for new users
10. Allows the user to edit a todo itempy


Note: I have never written unit tests before. I have also never deployed a webservice or written script to run on
the web / a server, therefore I am unsure of the tests to perform. Regarding the queries however, this is what I would 
test it against 

  list 
  list all complete
  #1 delete
  #5 done 
  add Eat cookies 
  list 
  list all complete 
  add Finish code 
  add Submit repo 
  list 
  list all complete 
  #2 finish
  #4 finish
  #1 delete
  list 
  list all complete
  add Buy milk 
  add Buy cookies
  add Drink water 
  search cookies 
  search milk 
  search water 
  clear all
  list 
  list all complete
