from django.core.management.base import BaseCommand
from document_processing.models import ChunkingMethod


class Command(BaseCommand):
    help = 'Populate the database with default chunking methods'

    def handle(self, *args, **options):
        """Create default chunking methods."""
        
        chunking_methods = [
            {
                'name': 'Unstructured.io Parser',
                'method_type': 'unstructured',
                'description': 'Structure-aware parsing using Unstructured.io for tables, headers, and complex layouts',
                'parameters': {
                    'strategy': 'auto',
                    'include_page_breaks': True,
                    'chunk_size': 5000,  # ~1000 words
                    'chunk_overlap': 500  # ~100 words
                }
            },
            {
                'name': 'LlamaParse Parser',
                'method_type': 'llamaparse',
                'description': 'GPT-4V powered parsing for complex documents with advanced structure recognition',
                'parameters': {
                    'result_type': 'markdown',
                    'language': 'en',
                    'chunk_size': 5000,  # ~1000 words
                    'chunk_overlap': 500  # ~100 words
                }
            },
            {
                'name': 'Hierarchical Chunking',
                'method_type': 'hierarchical',
                'description': 'Maintains document structure and hierarchical relationships between chunks',
                'parameters': {
                    'chunk_size': 5000,  # ~1000 words
                    'chunk_overlap': 500,  # ~100 words
                    'preserve_structure': True,
                    'hierarchical_depth': 3
                }
            },
            {
                'name': 'Semantic Chunking',
                'method_type': 'semantic',
                'description': 'Uses embeddings to determine semantic boundaries for more coherent chunks',
                'parameters': {
                    'chunk_size': 5000,  # ~1000 words
                    'semantic_threshold': 0.7,
                    'min_chunk_size': 500,  # ~100 words
                    'max_chunk_size': 10000,  # ~2000 words
                    'embedding_model': 'all-MiniLM-L6-v2'
                }
            },
            {
                'name': 'Financial Document Chunking',
                'method_type': 'financial',
                'description': 'Specialized chunking for financial documents with table and structure awareness',
                'parameters': {
                    'chunk_size': 5000,  # ~1000 words
                    'chunk_overlap': 500,  # ~100 words
                    'table_aware': True,
                    'preserve_financial_structure': True
                }
            },
            {
                'name': 'Recursive Character Splitting',
                'method_type': 'recursive',
                'description': 'Basic recursive character splitting with configurable separators',
                'parameters': {
                    'chunk_size': 5000,  # ~1000 words
                    'chunk_overlap': 500,  # ~100 words
                    'separators': ['\n\n', '\n', ' ', '']
                }
            },
            {
                'name': 'Sentence-based Splitting',
                'method_type': 'sentence',
                'description': 'Splits documents at sentence boundaries for natural language processing',
                'parameters': {
                    'chunk_size': 5000,  # ~1000 words
                    'chunk_overlap': 500,  # ~100 words
                    'sentence_separators': ['.', '!', '?']
                }
            },
            {
                'name': 'Token-based Splitting',
                'method_type': 'token',
                'description': 'Splits documents based on token count for precise size control',
                'parameters': {
                    'chunk_size': 5000,  # ~1000 words
                    'chunk_overlap': 500,  # ~100 words
                    'tokenizer': 'cl100k_base'
                }
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for method_data in chunking_methods:
            method, created = ChunkingMethod.objects.get_or_create(
                name=method_data['name'],
                defaults={
                    'method_type': method_data['method_type'],
                    'description': method_data['description'],
                    'parameters': method_data['parameters'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created chunking method: {method.name}')
                )
            else:
                # Update existing method
                method.method_type = method_data['method_type']
                method.description = method_data['description']
                method.parameters = method_data['parameters']
                method.is_active = True
                method.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated chunking method: {method.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated chunking methods. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
