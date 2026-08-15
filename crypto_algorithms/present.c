#include <stdint.h>
#include <stddef.h>

/* =========================================================
   PRESENT-80
   64-bit block, 80-bit key, 31 rounds
   ========================================================= */

static const uint8_t SBOX[16] = {
    0xC, 0x5, 0x6, 0xB,
    0x9, 0x0, 0xA, 0xD,
    0x3, 0xE, 0xF, 0x8,
    0x4, 0x7, 0x1, 0x2
};

static const uint8_t PBOX[64] = {
    0, 16, 32, 48,  1, 17, 33, 49,
    2, 18, 34, 50,  3, 19, 35, 51,
    4, 20, 36, 52,  5, 21, 37, 53,
    6, 22, 38, 54,  7, 23, 39, 55,
    8, 24, 40, 56,  9, 25, 41, 57,
    10, 26, 42, 58, 11, 27, 43, 59,
    12, 28, 44, 60, 13, 29, 45, 61,
    14, 30, 46, 62, 15, 31, 47, 63
};

/* =========================================================
   80-bit key
   ========================================================= */

typedef struct {
    uint16_t high;
    uint64_t low;
} present_key80;


/* =========================================================
   Key helpers
   ========================================================= */

static uint8_t key_get_bit(
    present_key80 key,
    int position
)
{
    if (position < 64) {
        return (uint8_t)((key.low >> position) & 1);
    }

    return (uint8_t)(
        (key.high >> (position - 64)) & 1
    );
}


static void key_set_bit(
    present_key80 *key,
    int position,
    uint8_t value
)
{
    if (position < 64) {

        if (value) {
            key->low |= ((uint64_t)1 << position);
        } else {
            key->low &= ~((uint64_t)1 << position);
        }

    } else {

        int p = position - 64;

        if (value) {
            key->high |= ((uint16_t)1 << p);
        } else {
            key->high &= ~((uint16_t)1 << p);
        }
    }
}


/* =========================================================
   Get leftmost 64 bits of 80-bit key
   ========================================================= */

static uint64_t get_round_key(
    present_key80 key
)
{
    return ((uint64_t)key.high << 48)
         | (key.low >> 16);
}


/* =========================================================
   Rotate 80-bit key left by 61 bits
   ========================================================= */

static present_key80 rotate_key_left_61(
    present_key80 key
)
{
    present_key80 result;

    result.high = 0;
    result.low = 0;

    for (int i = 0; i < 80; i++) {

        int old_position =
            (i - 61 + 80) % 80;

        uint8_t bit =
            key_get_bit(key, old_position);

        key_set_bit(
            &result,
            i,
            bit
        );
    }

    return result;
}


/* =========================================================
   Key S-box
   ========================================================= */

static void apply_key_sbox(
    present_key80 *key
)
{
    uint8_t sbox_input =
        (uint8_t)((key->high >> 12) & 0xF);

    uint8_t sbox_output =
        SBOX[sbox_input];

    key->high &= 0x0FFF;

    key->high |=
        ((uint16_t)sbox_output << 12);
}


/* =========================================================
   Add round counter
   ========================================================= */

static void add_round_counter(
    present_key80 *key,
    int round
)
{
    uint64_t value =
        ((uint64_t)round << 15);

    key->low ^= value;
}


/* =========================================================
   Generate all 32 round keys

   IMPORTANT:
   This happens ONCE per encryption operation,
   not once per block.
   ========================================================= */

static void generate_round_keys(
    present_key80 key,
    uint64_t round_keys[32]
)
{
    for (int i = 1; i <= 32; i++) {

        round_keys[i - 1] =
            get_round_key(key);

        key =
            rotate_key_left_61(key);

        apply_key_sbox(&key);

        add_round_counter(&key, i);
    }
}


/* =========================================================
   S-box layer
   ========================================================= */

static uint64_t substitution_layer(
    uint64_t state
)
{
    uint64_t result = 0;

    for (int j = 0; j < 16; j++) {

        uint8_t nibble =
            (uint8_t)(
                (state >> (j * 4)) & 0xF
            );

        result |=
            ((uint64_t)SBOX[nibble]
             << (j * 4));
    }

    return result;
}


/* =========================================================
   P-box layer
   ========================================================= */

static uint64_t permutation_layer(
    uint64_t state
)
{
    uint64_t result = 0;

    for (int j = 0; j < 64; j++) {

        uint64_t bit =
            (state >> j) & 1ULL;

        result |=
            (bit << PBOX[j]);
    }

    return result;
}


/* =========================================================
   Encrypt one block using PRE-COMPUTED round keys
   ========================================================= */

static uint64_t present_encrypt_with_round_keys(
    uint64_t plaintext,
    const uint64_t round_keys[32]
)
{
    uint64_t state = plaintext;

    for (int i = 0; i < 31; i++) {

        state ^= round_keys[i];

        state =
            substitution_layer(state);

        state =
            permutation_layer(state);
    }

    state ^= round_keys[31];

    return state;
}


/* =========================================================
   Export
   ========================================================= */

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif


/* =========================================================
   Existing single-block API

   We KEEP this so your old Python/C tests continue
   to work.
   ========================================================= */

EXPORT uint64_t present_encrypt(
    uint64_t plaintext,
    uint16_t key_high,
    uint64_t key_low
)
{
    present_key80 key;

    key.high = key_high;
    key.low = key_low;

    uint64_t round_keys[32];

    generate_round_keys(
        key,
        round_keys
    );

    return present_encrypt_with_round_keys(
        plaintext,
        round_keys
    );
}


/* =========================================================
   NEW: PRESENT CTR

   Encrypt an entire buffer in C.

   This generates the round keys ONCE and then
   reuses them for every block.

   input       = plaintext
   output      = ciphertext
   length      = number of bytes
   nonce       = initial 64-bit counter
   ========================================================= */

EXPORT void present_ctr(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t key_high,
    uint64_t key_low,
    uint64_t nonce
)
{
    present_key80 key;

    key.high = key_high;
    key.low = key_low;

    /* Generate round keys ONLY ONCE */
    uint64_t round_keys[32];

    generate_round_keys(
        key,
        round_keys
    );

    uint64_t counter = nonce;

    size_t offset = 0;

    while (offset < length) {

        /* Encrypt counter */
        uint64_t keystream =
            present_encrypt_with_round_keys(
                counter,
                round_keys
            );

        /* PRESENT outputs big-endian bytes */
        uint8_t stream[8];

        for (int i = 0; i < 8; i++) {
            stream[i] =
                (uint8_t)(
                    keystream >> (56 - i * 8)
                );
        }

        /* Number of bytes in this block */
        size_t remaining =
            length - offset;

        size_t block_size =
            remaining < 8 ? remaining : 8;

        /* XOR plaintext with keystream */
        for (size_t i = 0; i < block_size; i++) {

            output[offset + i] =
                input[offset + i] ^ stream[i];
        }

        /* Next CTR block */
        counter++;
        offset += block_size;
    }
}