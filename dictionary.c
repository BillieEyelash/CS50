// Implements a dictionary's functionality

#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <strings.h>
#include "dictionary.h"

// Represents a node in a hash table
typedef struct node
{
    char word[LENGTH + 1];
    struct node *next;
}
node;

void free_bucket(node *word);
uint32_t MurmurHash2(const void *key, int len, uint32_t seed);

// Number of buckets in hash table
const unsigned int N = 143091;
// Number of words in the hash table
unsigned int numWords = 0;

// Hash table
node *table[N];

// Returns true if word is in dictionary, else false
bool check(const char *word)
{
    //char buffer[LENGTH];
    unsigned int hashed = hash(word);
    node *cursor = table[hashed];
    while (cursor != NULL)
    {
        if (strcasecmp(cursor->word, word) == 0)
        {
            return true;
        }
        cursor = cursor->next;
    }
    return false;
}

// Hashes word to a number
unsigned int hash(const char *word)
{
    char buffer[LENGTH + 1];
    for (int i = 0; i < LENGTH; i++)
    {
        buffer[i] = tolower(word[i]);
        if (buffer[i] == '\0')
        {
            break;
        }
    }
    unsigned int hashed = MurmurHash2(buffer, strlen(buffer), 5);
    return hashed % N;
}

// Loads dictionary into memory, returning true if successful, else false
bool load(const char *dictionary)
{
    // Open file and check if it worked
    FILE *file = fopen(dictionary, "r");
    if (file == NULL)
    {
        fclose(file);
        return false;
    }

    char buffer[LENGTH + 1];
    fscanf(file, "%s", buffer);
    // Iterate over words in file until get EOF
    while (!feof(file))
    {
        // Create new node and copy word into it
        node *word = malloc(sizeof(node));
        if (word == NULL)
        {
            fclose(file);
            return false;
        }

        strcpy(word->word, buffer);
        numWords++;

        // Hash word and add to beginning of bucket
        unsigned int hashed = hash(buffer);
        word->next = table[hashed];
        table[hashed] = word;
        // Go to next word
        fscanf(file, "%s", buffer);
    }
    fclose(file);
    return true;
}

// Returns number of words in dictionary if loaded, else 0 if not yet loaded
unsigned int size(void)
{
    return numWords;
}

// Unloads dictionary from memory, returning true if successful, else false
bool unload(void)
{
    for (int i = 0; i < N; i++)
    {
        free_bucket(table[i]);
    }
    return true;
}

// Recursively free a single bucket in a hash table
void free_bucket(node *word)
{
    if (word == NULL)
    {
        return;
    }
    free_bucket(word->next);
    free(word);
}


// MurmurHash2, by Austin Appleby
// Note - This code makes a few assumptions about how your machine behaves -
// 1. We can read a 4-byte value from any address without crashing
// 2. sizeof(int) == 4
//
// And it has a few limitations -
//
// 1. It will not work incrementally.
// 2. It will not produce the same results on little-endian and big-endian
//    machines.
uint32_t MurmurHash2(const void *key, int len, uint32_t seed)
{
    // 'm' and 'r' are mixing constants generated offline.
    // They're not really 'magic', they just happen to work well.
    const uint32_t m = 0x5bd1e995;
    const int r = 24;
    // Initialize the hash to a 'random' value
    uint32_t h = seed ^ len;
    // Mix 4 bytes at a time into the hash
    const unsigned char *data = (const unsigned char *)key;
    while (len >= 4)
    {
        uint32_t k = *(uint32_t *)data;

        k *= m;
        k ^= k >> r;
        k *= m;

        h *= m;
        h ^= k;

        data += 4;
        len -= 4;
    }

    // Handle the last few bytes of the input array

    switch (len)
    {
        case 3:
            h ^= data[2] << 16;
        case 2:
            h ^= data[1] << 8;
        case 1:
            h ^= data[0];
            h *= m;
    }

    // Do a few final mixes of the hash to ensure the last few
    // bytes are well-incorporated
    h ^= h >> 13;
    h *= m;
    h ^= h >> 15;

    return h;
}