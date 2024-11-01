# Author: Shelby Falde
# Course: CS131

from brewparse import parse_program
from intbase import *

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        # Since functions (at the top level) can be created anywhere, we'll just do a search for function definitions and assign them 'globally'
        # alternate name: func_nodes
        self.func_defs = []
        

    def run(self, program):

        ast = parse_program(program) # returns list of function nodes
        #self.output(ast)
        self.variable_name_to_value = {} # dict to hold vars
        self.func_defs = self.get_func_defs(ast)
        main_func_node = self.get_main_func_node(ast)
        #self.output(main_func_node)
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
        for statement_node in func_node.dict['statements']:
            #self.output(statement_node)
            self.run_statement(statement_node)
    

    def run_statement(self, statement_node):
        if self.is_definition(statement_node):
            #self.output(f"doing definition: {statement_node}")
            self.do_definition(statement_node)
        elif self.is_assignment(statement_node):
            self.do_assignment(statement_node)
        elif self.is_func_call(statement_node):
            self.do_func_call(statement_node)
    
    def is_definition(self, statement_node):
        return (True if statement_node.elem_type == "vardef" else False)
    def is_assignment(self, statement_node):
        return (True if statement_node.elem_type == "=" else False)
    def is_func_call(self, statement_node):
        return (True if statement_node.elem_type == "fcall" else False)


    def do_definition(self, statement_node):
        # just add to var_name_to_value dict
        target_var_name = self.get_target_variable_name(statement_node)
        self.variable_name_to_value[target_var_name] = None
        

    def do_assignment(self, statement_node):
        target_var_name = self.get_target_variable_name(statement_node)
        if not self.var_name_exists(target_var_name):
            # error called for not declared var, and states it
            super().error(ErrorType.NAME_ERROR, ("variable used and not declared: " + target_var_name), )
        source_node = self.get_expression_node(statement_node)
        resulting_value = self.evaluate_expression(source_node)
        self.variable_name_to_value[target_var_name] = resulting_value
        # below actually quite important during testing
        #self.output(self.variable_name_to_value[target_var_name])

    # Check if function is defined
    def check_valid_func(self, func_call):
        for func in self.func_defs:
            if func.dict['name'] == func_call:
                return True
        return False

    # Allows function overloading by first searching for func_defs for a matching name and arg length
    def get_func_def(self, func_call, arg_len):
        for func in self.func_defs:
            if func.dict['name'] == func_call and len(func.dict['args']) == arg_len:
                return func
        # Already check if func exists before calling
        # So, must not have correct args.
        super().error(ErrorType.NAME_ERROR,
                       f"Incorrect amount of arguments given: {arg_len} ",
                       )
    

    def do_func_call(self, statement_node):
        func_call = statement_node.dict['name']
        #self.output(func_call)
        if func_call == "print":
            output = ""
            # loop through each arg in args list for print, evaluate their expressions, concat, and output.
            for arg in statement_node.dict['args']:
                # note, cant concat unles its str type
                output += str(self.evaluate_expression(arg))
            # THIS IS 1/2 OF ONLY REAL SELF.OUTPUT
            self.output(output)
        elif func_call == "inputi":
            output = ""
            for arg in statement_node.dict['args']:
                output += str(self.evaluate_expression(arg))
            # THIS IS 2/2 OF ONLY REAL SELF.OUTPUT
            if output != "":
                self.output(output)
            return self.get_input()
        else:
            ## USER-DEFINED FUNCTION ##
            # Check if function is defined
            if not self.check_valid_func(func_call):
                super().error(ErrorType.NAME_ERROR,
                                f"Function {func_call} was not found",
                                )
            # If reach here, function must be valid; grab function definition
            func_def = self.get_func_def(func_call, len(statement_node.dict['args']))
            
            ##### Start Function Call ######
            # Copilot suggested this idea to just copy the calling functions variables
            # Citing copilot for just direct line below. AI code count: 1 line
            parent_vardefs = self.variable_name_to_value.copy()

            #### START SCOPE ####
            scoped_vars = {}

            # Assign parameters to the local variable dict

            args = statement_node.dict['args'] # passed in arguments
            params = func_def.dict['args'] # function parameters

            for i in range(0,len(params)):
                # Assign to local variable list
                # Check if var exists in calling function

                scoped_vars[params[i].dict['name']] = self.evaluate_expression(args[i])
    
            # replace calling vars with new scoped vars (parameters)
            self.variable_name_to_value = scoped_vars
            # self.output(f"New In-scope vars only: {self.variable_name_to_value}")
            self.run_func(func_def)
            
            # NOTE: for if or for, remember to check the copied vars above

            #### END SCOPE ####
            #self.output(f"function definition: {func_def}")
            statement_nodes = func_def.dict['statements']
            for statement in statement_nodes:
                if statement.elem_type == "return":
                    return_node = statement
                    return self.evaluate_expression(return_node.dict['expression'])

            

            # Re-establish old values.
            self.variable_name_to_value = parent_vardefs
                            
            ##### End Function Call ######
    

    def get_target_variable_name(self, statement_node):
        return statement_node.dict['name']
    def var_name_exists(self, varname):
        return True if varname in self.variable_name_to_value.keys() else False
    def get_expression_node(self, statement_node):
        return statement_node.dict['expression']
    

    def is_value_node(self, expression_node):
        return True if (expression_node.elem_type in ["int", "string"]) else False
    def is_variable_node(self, expression_node):
        return True if (expression_node.elem_type == "var") else False
    def is_binary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["+", "-"]) else False
    def is_unary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["neg", "!"]) else False

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
        elif self.is_func_call(expression_node):
            return self.do_func_call(expression_node)

    def get_value(self, expression_node):
        # Returns value assigned to key 'val'
        return expression_node.dict['val']
    def get_value_of_variable(self, expression_node):
        # returns value under the variable name provided.
        # NEED TO CATCH: if var NOT ASSIGNED VALUE YET: ex: {var x; print(x);}
        # NOTE this is how its done in barista, feels bad if we were to add concatonation in future, or something else. NOT FUTURE PROOF.
        val = self.variable_name_to_value[expression_node.dict['name']]
        if val is None:
            return 0
        else:
            return val


    # + or -
    def evaluate_binary_operator(self, expression_node):
        # can *only* be + or -.. for now.
        # returns arg1 - arg2 (allows for nested/recursive calls should something like 5+8-6 happen)
        # self.output(expression_node)
        if expression_node.elem_type == "+":
            return (self.evaluate_expression(expression_node.dict['op1']) + self.evaluate_expression(expression_node.dict['op2']))
        elif expression_node.elem_type == "-":
            return (self.evaluate_expression(expression_node.dict['op1']) - self.evaluate_expression(expression_node.dict['op2']))

    def evaluate_unary_operator(self, expression_node):
        # can be neg (-b) or  '!' for boolean
        return 0


    # No more functions remain... for now... :)

program = """
            func foo() {
                var y;
                y = 5;
                return 17 + y;
            }

            func bar() {
                return;
            }

            func main() {
                var val;
                val = nil;
                print(foo());
            }          
            """
interpreter = Interpreter()
interpreter.run(program)