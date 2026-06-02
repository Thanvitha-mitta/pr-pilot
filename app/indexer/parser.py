from tree_sitter import Language, Parser
import tree_sitter_typescript as tsts

class CodeParser:
    def __init__(self):
        # Initialize the Tree-sitter Language and Parser for TypeScript
        self.ts_language = Language(tsts.language_typescript())
        self.parser = Parser(self.ts_language)

    def extract_functions(self, code_bytes: bytes) -> list[str]:
        """Parses the code and extracts intact functions/methods using recursive AST walking."""
        tree = self.parser.parse(code_bytes)
        chunks =[]
        
        def walk(node):
            # Capture standard functions and class methods
            if node.type in ['function_declaration', 'method_definition']:
                chunk = code_bytes[node.start_byte:node.end_byte].decode('utf-8')
                chunks.append(chunk)
                
            # Capture arrow functions (e.g., const myFunc = () => {...})
            elif node.type == 'variable_declarator':
                for child in node.children:
                    if child.type == 'arrow_function':
                        chunk = code_bytes[node.start_byte:node.end_byte].decode('utf-8')
                        chunks.append(chunk)
                        break
            
            # Recursively walk through all child nodes
            for child in node.children:
                walk(child)

        # Start the traversal from the root of the file
        walk(tree.root_node)
        
        return chunks

# ==========================================
# TEST BLOCK
# ==========================================
if __name__ == "__main__":
    sample_code = b"""
    import { something } from 'somewhere';

    // We only want to extract the functions, not the imports or random comments!
    function calculateTotal(price: number, tax: number): number {
        return price + tax;
    }

    class User {
        getUserData(id: string) {
            console.log("Fetching user...");
            return { id: id, name: "Thanvitha" };
        }
    }
    """

    print("Parsing code using Abstract Syntax Tree (AST)...")
    parser = CodeParser()
    functions = parser.extract_functions(sample_code)

    print(f"Found {len(functions)} functions/methods:\n")
    for i, func in enumerate(functions):
        print(f"--- Chunk {i+1} ---")
        print(func)
        print("-" * 15 + "\n")