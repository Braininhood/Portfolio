// dictionary.c
#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "dictionary.h"

// Represents a node in a hash table
typedef struct node
{
    char word[LENGTH + 1];
    struct node *next;
} node;

// Number of buckets in hash table
const unsigned int N = 10000; // Increase number of buckets for better performance

// Hash table
node *table[N];

// Keeps track of the total number of words in the dictionary
unsigned int word_count = 0;

// Hashes word to a number
unsigned int hash(const char *word)
{
    // Hash function based on the djb2 algorithm
    unsigned long hash_value = 5381;
    int c;
    while ((c = *word++))
    {
        hash_value = ((hash_value << 5) + hash_value) + tolower(c); // hash * 33 + c
    }
    return hash_value % N;
}

// Loads dictionary into memory, returning true if successful, else false
bool load(const char *dictionary)
{
    // Open the dictionary file
    FILE *file = fopen(dictionary, "r");
    if (file == NULL)
    {
        return false;
    }

    // Buffer to store each word
    char word[LENGTH + 1];

    // Read each word from the dictionary
    while (fscanf(file, "%45s", word) != EOF)
    {
        // Create a new node for each word
        node *new_node = malloc(sizeof(node));
        if (new_node == NULL)
        {
            return false;
        }
        strcpy(new_node->word, word);
        new_node->next = NULL;

        // Hash the word to find the appropriate index
        unsigned int index = hash(word);

        // Insert the node into the hash table at the index
        new_node->next = table[index];
        table[index] = new_node;

        // Increment the word count
        word_count++;
    }

    // Close the dictionary file
    fclose(file);
    return true;
}

// Returns number of words in dictionary if loaded, else 0 if not yet loaded
unsigned int size(void)
{
    return word_count;
}

// Returns true if word is in dictionary, else false
bool check(const char *word)
{
    // Hash the word to get the index
    unsigned int index = hash(word);

    // Traverse the linked list at the hash table index
    for (node *cursor = table[index]; cursor != NULL; cursor = cursor->next)
    {
        if (strcasecmp(cursor->word, word) == 0)
        {
            return true;
        }
    }
    return false;
}

// Unloads dictionary from memory, returning true if successful, else false
bool unload(void)
{
    // Iterate over each index in the hash table
    for (unsigned int i = 0; i < N; i++)
    {
        node *cursor = table[i];
        while (cursor != NULL)
        {
            node *temp = cursor;
            cursor = cursor->next;
            free(temp);
        }
    }
    return true;
}
