# Author: Shelby Falde
# Course: CS131

from brewparse import *
from intbase import *

nil = Element("nil")

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        # Since functions (at the top level) can be created anywhere, we'll just do a search for function definitions and assign them 'globally'
        # alternate name: func_nodes
        self.func_defs = []
        # copilot: (+1)
        self.variable_scope_stack = [{}] # Stack to hold variable scopes
        

    def run(self, program):

        ast = parse_program(program) # returns list of function nodes
        self.func_defs = self.get_func_defs(ast)
        main_func_node = self.get_main_func_node(ast)
        self.run_func(main_func_node)

    # grabs all globally defined functions to call when needed.
    def get_func_defs(self, ast):
        # returns functions sub-dict, 'functions' is key
        
        return ast.dict['functions']

    # returns 'main' func node from the dict input.
    def get_main_func_node(self, ast):

        # checks for function whose name is 'main'
        for func in self.func_defs:
            
            if func.dict['name'] == "main":
                return func
            
        
        # define error for 'main' not found.
        super().error(ErrorType.NAME_ERROR, "No main() function was found")


    # self explanatory
    def run_func(self, func_node):
        # statements key for sub-dict.
        ### BEGIN FUNC SCOPE ###
        self.variable_scope_stack.append({})
        
        return_value = nil
        #self.output(f"function: {func_node}")
        for statement in func_node.dict['statements']:
            return_value = self.run_statement(statement)
            #self.output(f"returned: {return_value}")
            # check if statement results in a return, and return a return statement with 
            if isinstance(return_value, Element) and return_value.elem_type == "return":
                # Return the value, dont need to continue returning.
                #self.output(return_value)
                #self.output(f"statement: {statement}, \n vars: {self.variable_scope_stack}")
                #self.output(self.variable_scope_stack)
                self.variable_scope_stack.pop()
                #self.output(self.variable_scope_stack)
                return return_value.get("value")
            if return_value is not nil:
                break
      
        ### END FUNC SCOPE ###
        #self.output(self.variable_scope_stack)
        self.variable_scope_stack.pop()
        #self.output(self.variable_scope_stack)
        return return_value
    

    def run_statement(self, statement_node):
        #print(f"Running statement: {statement_node}")
        if self.is_definition(statement_node):
            #self.output(f"doing definition: {statement_node}")
            self.do_definition(statement_node)
        elif self.is_assignment(statement_node):
            self.do_assignment(statement_node)
        elif self.is_func_call(statement_node):
            #self.output(f"func {statement_node} returns: {self.do_func_call(statement_node)}")
            return self.do_func_call(statement_node)
        elif self.is_return_statement(statement_node):
            #self.output(f"ret {statement_node} returns: {self.do_return_statement(statement_node)}")
            return self.do_return_statement(statement_node)
        elif self.is_if_statement(statement_node):
            #self.output(f"if {statement_node} returns: {self.is_if_statement(statement_node)}")
            return self.do_if_statement(statement_node)
        elif self.is_for_loop(statement_node):
            #self.output(f"for {statement_node} returns: {self.do_for_loop(statement_node)}")
            return self.do_for_loop(statement_node)
        return nil

    
    def is_definition(self, statement_node):
        return (True if statement_node.elem_type == "vardef" else False)
    def is_assignment(self, statement_node):
        return (True if statement_node.elem_type == "=" else False)
    def is_func_call(self, statement_node):
        
        return (True if statement_node.elem_type == "fcall" else False)
    def is_return_statement(self, statement_node):
        return (True if statement_node.elem_type == "return" else False)
    def is_if_statement(self, statement_node):
        return (True if statement_node.elem_type == "if" else False)
    def is_for_loop(self, statement_node):
        return (True if statement_node.elem_type == "for" else False)


    def do_definition(self, statement_node):
        # just add to var_name_to_value dict
        target_var_name = self.get_target_variable_name(statement_node)
        # Copilot (+1)
        if target_var_name in self.variable_scope_stack[-1]:
            super().error(ErrorType.NAME_ERROR, f"Variable {target_var_name} defined more than once",)
        else:
            #self.output(f"vars: {self.variable_scope_stack}")
            self.variable_scope_stack[-1][target_var_name] = None
        #self.variable_scope_stack[-1][target_var_name] = None
        

    def do_assignment(self, statement_node):
        
        target_var_name = self.get_target_variable_name(statement_node)
        # Copilot (+5)
        #self.output(self.variable_scope_stack)
        for scope in reversed(self.variable_scope_stack): 
            if target_var_name in scope: 
                # Does not evaluate until after checking if valid variable
                source_node = self.get_expression_node(statement_node)
                resulting_value = self.evaluate_expression(source_node)
                scope[target_var_name] = resulting_value 
                #self.output(self.variable_scope_stack)
                return
        super().error(ErrorType.NAME_ERROR, f"variable used and not declared: {target_var_name}")

    # Check if function is defined
    def check_valid_func(self, func_call):
        for func in self.func_defs:
            if func.dict['name'] == func_call:
                return True
        return False

    # Allows function overloading by first searching for func_defs for a matching name and arg length
    def get_func_def(self, func_call, arg_len):
        #self.output(f"call: {func_call}, args: {arg_len}")
        for func in self.func_defs:
            if func.dict['name'] == func_call and len(func.dict['args']) == arg_len:
                return func
        # Already check if func exists before calling
        # So, must not have correct args.
        super().error(ErrorType.NAME_ERROR,
                       f"Incorrect amount of arguments given: {arg_len} ",
                       )
    

    def do_func_call(self, statement_node):
        #self.output(statement_node)
        func_call = statement_node.dict['name']
        if func_call == "print":
            output = ""
            # loop through each arg in args list for print, evaluate their expressions, concat, and output.
            for arg in statement_node.dict['args']:
                # note, cant concat unles its str type
                output += str(self.evaluate_expression(arg))
            # THIS IS 1/3 OF ONLY REAL SELF.OUTPUT
            self.output(output)
            return nil
        elif func_call == "inputi":

            ## NOTE: this may come up in the git history as 'copy and pasted' but its because 
            # my git repo didnt have this inputi() version, but my submission for project 1 did.
            # too many inputi params
            if len(statement_node.dict['args']) > 1:
                super().error(ErrorType.NAME_ERROR,f"No inputi() function found that takes > 1 parameter",)
            elif len(statement_node.dict['args']) == 1:
                arg = statement_node.dict['args'][0]
                # THIS IS 2/3 OF ONLY REAL SELF.OUTPUT
                self.output(self.evaluate_expression(arg))
                #output = str(self.evaluate_expression(arg))

            user_in = super().get_input()
            try:
                user_in = int(user_in)
                return user_in
            except:
                return user_in
        
        # same as inputi but for strings
        elif func_call == "inputs":
            # too many inputi params
            if len(statement_node.dict['args']) > 1:
                super().error(ErrorType.NAME_ERROR,f"No inputi() function found that takes > 1 parameter",)
            elif len(statement_node.dict['args']) == 1:
                arg = statement_node.dict['args'][0]
                # THIS IS 3/3 OF ONLY REAL SELF.OUTPUT
                self.output(self.evaluate_expression(arg))
                #output = str(self.evaluate_expression(arg))

            user_in = super().get_input()
            try:
                user_in = int(user_in)
                return user_in
            except:
                return user_in
        else:
            ## USER-DEFINED FUNCTION ##
            # Check if function is defined
            #self.output(f"func statement: {statement_node}")
            if not self.check_valid_func(func_call):
                super().error(ErrorType.NAME_ERROR,
                                f"Function {func_call} was not found",
                                )
            # If reach here, function must be valid; grab function definition
            
            func_def = self.get_func_def(func_call, len(statement_node.dict['args']))
            ##### Start Function Call ######

            #### START SCOPE ####
            self.variable_scope_stack.append({})

            # Assign parameters to the local variable dict
            args = statement_node.dict['args'] # passed in arguments
            params = func_def.dict['args'] # function parameters

            # intialize paramas, and then assign to them each arg in order
            for i in range(0,len(params)):
                # Assign to local variable list

                # define param
                var_name = params[i].dict['name']
                self.variable_scope_stack[-1][var_name] = self.evaluate_expression(args[i])
                # self.do_assignment(self.evaluate_expression(args[i]))
                #scoped_vars[params[i].dict['name']] = self.evaluate_expression(args[i])
            
            return_value = self.run_func(func_def)
            #self.output(return_value)
            # NOTE: for if or for, remember to check the copied vars above
            
            #### END SCOPE ####
            self.variable_scope_stack.pop()
            return return_value
                            
            ##### End Function Call ######
    
    def do_return_statement(self, statement_node):
        #self.output(statement_node)
        if not statement_node.dict['expression']:
            #return 'nil' Element
            # I had the idea, Copilot (+1) showed me how to assign a val
            return Element("return", value=nil)
        return self.evaluate_expression(statement_node.dict['expression'])

    # Scope rules: Can access parent calling vars, but vars they create are deleted after scope.
    # So, keep track of what vars were before, and after end of clause, wipe those variables.
    def do_if_statement(self, statement_node):
        condition = statement_node.dict['condition']
        condition = self.evaluate_expression(condition)
        # error if condition is non-boolean
        if type(condition) is not bool:
            super().error(ErrorType.TYPE_ERROR, "Condition is not of type bool",)
        statements = statement_node.dict['statements']
        else_statements = statement_node.dict['else_statements']

        ### BEGIN IF SCOPE ###
        # Copilot (+1)
        self.variable_scope_stack.append({})
        if condition:
            for statement in statements:
                #self.output(statement)
                return_value = self.run_statement(statement)
                #self.output(return_value)
     
                if isinstance(return_value, Element) and return_value.elem_type == "return":
                    #end scope early and return
                    self.variable_scope_stack.pop()
                    return Element("return", value=return_value.get("value"))
                elif return_value is not nil:
                    self.variable_scope_stack.pop()
                    return Element("return", value=return_value)
                    # if return needed, stop running statements, immediately return the value.
        else:
            if else_statements:
                for else_statement in else_statements:
                    return_value = self.run_statement(else_statement)
                    
                    if isinstance(return_value, Element) and return_value.elem_type == "return":
                        #end scope early and return
                        self.variable_scope_stack.pop()
                        return Element("return", value=return_value.get("value"))
                    elif return_value is not nil:
                        self.variable_scope_stack.pop()
                        return Element("return", value=return_value)
        ### END IF SCOPE ###

        # Copilot (+1)
        self.variable_scope_stack.pop()
        return nil


    def do_for_loop(self, statement_node):
        # Run initializer
        init_node = statement_node.dict['init']
        self.run_statement(init_node)
        update = statement_node.dict['update']
        condition = statement_node.dict['condition']
        statements = statement_node.dict['statements']
        
        #self.output(self.variable_scope_stack)
        # Run the loop again (exits on condition false)
        while self.evaluate_expression(condition):
            if type(self.evaluate_expression(condition)) is not bool:
                super().error(ErrorType.TYPE_ERROR, "Condition is not of type bool",)
            
            ### BEGIN VAR SCOPE ###
            self.variable_scope_stack.append({})

            #self.output(f"RUNNING LOOP.")
            for statement in statements:
                return_value = self.run_statement(statement)
                # I dont think i can just do 'if return_value:' incase its an int
                if isinstance(return_value, Element) and return_value.elem_type == "return":
                    #self.output(f"Presumably breaking. Value: {return_value} at statement: {statement_node}")
                    #end scope early and return
                    self.variable_scope_stack.pop()
                    return Element("return", value=return_value.get("value"))
                elif return_value is not nil:
                    return Element("return", value=return_value)

            ### END VAR SCOPE ###
            self.variable_scope_stack.pop()
            update = statement_node.dict['update']
            self.run_statement(update)

        #self.output(condition)
        #self.output(self.variable_scope_stack)
        #self.output("exiting for")
        return nil
        
        
    # helper functions
    def get_target_variable_name(self, statement_node):
        return statement_node.dict['name']
    # Copilot (-2)
    # def var_name_exists(self, varname):
    #     return True if varname in self.variable_name_to_value.keys() else False
    def get_expression_node(self, statement_node):
        return statement_node.dict['expression']
    

    # basically pseudocode, self-explanatory
    def is_value_node(self, expression_node):
        return True if (expression_node.elem_type in ["int", "string", "bool", "nil"]) else False
    def is_variable_node(self, expression_node):
        return True if (expression_node.elem_type == "var") else False
    def is_binary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["+", "-", "*", "/"]) else False
    def is_unary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["neg", "!"]) else False
    def is_comparison_operator(self, expression_node):
        return True if (expression_node.elem_type in ['==', '<', '<=', '>', '>=', '!=']) else False
    def is_binary_boolean_operator(self, expression_node):
        return True if (expression_node.elem_type in ['&&', '||']) else False


    # basically pseudcode, self-explanatory
    def evaluate_expression(self, expression_node):
        #self.output(f"expressing: {expression_node}")
        if self.is_value_node(expression_node):
            return self.get_value(expression_node)
        elif self.is_variable_node(expression_node):
            return self.get_value_of_variable(expression_node)
        elif self.is_binary_operator(expression_node):
            return self.evaluate_binary_operator(expression_node)
        elif self.is_unary_operator(expression_node):
            return self.evaluate_unary_operator(expression_node)
        elif self.is_comparison_operator(expression_node):
            return self.evaluate_comparison_operator(expression_node)
        elif self.is_binary_boolean_operator(expression_node):
            return self.evaluate_binary_boolean_operator(expression_node)
        elif self.is_func_call(expression_node):
            return self.do_func_call(expression_node)

    def get_value(self, expression_node):
        # Returns value assigned to key 'val'
        if expression_node.elem_type == "nil":
            return nil
        return expression_node.dict['val']
    def get_value_of_variable(self, expression_node):
        # returns value under the variable name provided.
        
        if expression_node == 'nil':
            return nil
        
        # Copilot (+4)
        var_name = expression_node.dict['name']
        for scope in reversed(self.variable_scope_stack): 
            if var_name in scope: 
                val = scope[var_name] 
                if val is nil:
                    return nil
                else: 
                    return val 
        # self.output(self.variable_scope_stack)
        super().error(ErrorType.NAME_ERROR, f"variable '{var_name}' used and not declared")


    # + or -
    def evaluate_binary_operator(self, expression_node):
        # can *only* be +, -, *, / for now.

        eval1 = self.evaluate_expression(expression_node.dict['op1'])
        eval2 = self.evaluate_expression(expression_node.dict['op2'])
        # for all operators other than + (for concat), both must be of type 'int'
        if (expression_node.elem_type != "+") and not (isinstance(eval1, int) and isinstance(eval2,int)):
            super().error(ErrorType.TYPE_ERROR, "Arguments must be of type 'int'.")
        # note, the line below looked like above 'isinstance' but i just made it this because instance was bugging (probably just had bad () lol)
        # if + and ...
        elif not ((type(eval1) == int and type(eval2) == int) or (type(eval1) == str and type(eval2) == str)):
            super().error(ErrorType.TYPE_ERROR, "Types for + must be both of type int or string.")

        #self.output(f"{expression_node.elem_type} #1: {eval1} \n #2: {eval2}")
        if expression_node.elem_type == "+":
            return (eval1 + eval2)
        elif expression_node.elem_type == "-":
            return (eval1 - eval2)
        elif expression_node.elem_type == "*":
            return (eval1 * eval2)
        elif expression_node.elem_type == "/":
            # integer division
            return (eval1 // eval2)


    def evaluate_unary_operator(self, expression_node):
        # can be 'neg' (-b) or  '!' for boolean
        #self.output(expression_node)
        eval = self.evaluate_expression(expression_node.dict['op1'])
        if expression_node.elem_type == "neg":
            return -(eval)
        if expression_node.elem_type == "!":
            if not (type(eval) == bool):
                super().error(ErrorType.TYPE_ERROR, "'Not' can only be used on boolean values.")
            return not (eval)
        
    # there's probably a better way to do this but oh well
    def evaluate_comparison_operator(self, expression_node):
        eval1 = self.evaluate_expression(expression_node.dict['op1'])
        eval2 = self.evaluate_expression(expression_node.dict['op2'])
        #self.output(f"expression: {expression_node}")
        #self.output(f"== #1: {expression_node.dict['op1']} \n #2: {expression_node.dict['op2']}")
        #self.output(f"== #1: {eval1} \n #2: {eval2}")
        # != and == can compare different types.
        if (expression_node.elem_type not in ["!=", "=="]) and (type(eval1) is not type(eval2)):
            super().error(ErrorType.TYPE_ERROR, "Comparison arguments must be of same type.")
        match expression_node.elem_type:
            case '<':
                return (eval1 < eval2)
            case '<=':
                return (eval1 <= eval2)
            case '==':
                return (eval1 == eval2)
            case '>=':
                return (eval1 >= eval2)
            case '>':
                return (eval1 > eval2)
            case '!=': 
                return (eval1 != eval2)  
    
    def evaluate_binary_boolean_operator(self, expression_node):
        eval1 = self.evaluate_expression(expression_node.dict['op1'])
        eval2 = self.evaluate_expression(expression_node.dict['op2'])
        # forces evaluation on both (strict evaluation)
        #self.output(f"&& #1: {eval1} \n #2: {eval2}")
        eval1 = bool(eval1)
        eval2 = bool(eval2)
        #self.output(f"&& #1: {eval1} \n #2: {eval2}")
        
        #self.output(f"expression: {expression_node}")
        match expression_node.elem_type:
            case '&&':
                return (eval1 and eval2)
            case '||':
                return (eval1 or eval2)
    # No more functions remain... for now... :)

#DEBUGGING
program = """
func foo() { 
 print("hello");
 /* no explicit return command */
}

func bar() {
  return;  /* no return value specified */
}

func main() {
   var val;
   val = nil;
   if (foo() == val && bar() == nil) { print("this should print!"); }
}


"""
interpreter = Interpreter()
interpreter.run(program)

# ret = Element("return", value="hiasdas `1239")
# num = 6
# lst = [ret, num]
# for thing in lst:
#     if isinstance(thing, Element) and thing.elem_type == "return":
#         print(ret.get("value"))