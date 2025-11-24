#!/usr/bin/env python3
"""
Testing Performance ASCON Encryption & Decryption
Mengukur waktu enkripsi, dekripsi, throughput, dan konsumsi memori
"""

import ascon
import time
import json
import statistics
import sys

# ===== KONFIGURASI =====
KEY = "asconciphertest1".encode('utf-8')  # 16 bytes
NONCE = "asconcipher1test".encode('utf-8')  # 16 bytes
ASSOCIATED_DATA = b"ASCON"
VARIANT = "Ascon-128"

# Jumlah iterasi untuk testing
NUM_ITERATIONS = 1000

# ===== DATA TESTING =====
# Simulasi data sensor dalam berbagai ukuran
test_data = {
    "small": json.dumps({
        "id": "ESP8266_HCSR04",
        "distance": 25,
        "unit": "cm"
    }),
    "medium": json.dumps({
        "id": "ESP8266_HCSR04_Client",
        "count": 100,
        "distance": 25,
        "timestamp": 12345678,
        "unit": "cm",
        "sensor_type": "HC-SR04",
        "location": "Room A"
    }),
    "large": json.dumps({
        "id": "ESP8266_HCSR04_Client",
        "count": 100,
        "distance": 25,
        "timestamp": 12345678,
        "unit": "cm",
        "sensor_type": "HC-SR04",
        "location": "Room A",
        "additional_data": "x" * 200  # Tambahan data untuk ukuran lebih besar
    })
}

# ===== FUNGSI TESTING =====
def test_encryption(plaintext, num_iter):
    """Test enkripsi"""
    encryption_times = []
    ciphertext = None
    
    for i in range(num_iter):
        start = time.perf_counter()
        ciphertext = ascon.demo_aead_c(VARIANT, plaintext, KEY, NONCE, ASSOCIATED_DATA)
        end = time.perf_counter()
        encryption_times.append((end - start) * 1000)  # Convert to ms
    
    return encryption_times, ciphertext

def test_decryption(ciphertext, num_iter):
    """Test dekripsi"""
    decryption_times = []
    
    for i in range(num_iter):
        start = time.perf_counter()
        plaintext = ascon.demo_aead_p(VARIANT, ciphertext)
        end = time.perf_counter()
        decryption_times.append((end - start) * 1000)  # Convert to ms
        
        if plaintext is None:
            print("❌ Decryption failed!")
            return None
    
    return decryption_times

def calculate_stats(times):
    """Hitung statistik"""
    return {
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0
    }

def print_results(data_type, plaintext, enc_stats, dec_stats, enc_times, dec_times):
    """Print hasil testing"""
    print(f"\n{'='*70}")
    print(f"📊 RESULTS - {data_type.upper()} DATA")
    print(f"{'='*70}")
    print(f"📏 Plaintext size: {len(plaintext)} bytes")
    print(f"🔢 Iterations: {len(enc_times)}")
    
    print(f"\n🔐 ENCRYPTION:")
    print(f"   ⏱️  Min time:    {enc_stats['min']:.4f} ms")
    print(f"   ⏱️  Max time:    {enc_stats['max']:.4f} ms")
    print(f"   ⏱️  Mean time:   {enc_stats['mean']:.4f} ms")
    print(f"   ⏱️  Median time: {enc_stats['median']:.4f} ms")
    print(f"   📊 Std dev:     {enc_stats['stdev']:.4f} ms")
    
    print(f"\n🔓 DECRYPTION:")
    print(f"   ⏱️  Min time:    {dec_stats['min']:.4f} ms")
    print(f"   ⏱️  Max time:    {dec_stats['max']:.4f} ms")
    print(f"   ⏱️  Mean time:   {dec_stats['mean']:.4f} ms")
    print(f"   ⏱️  Median time: {dec_stats['median']:.4f} ms")
    print(f"   📊 Std dev:     {dec_stats['stdev']:.4f} ms")
    
    # Throughput
    throughput_enc = (len(plaintext) / (enc_stats['mean'] / 1000)) / 1024  # KB/s
    throughput_dec = (len(plaintext) / (dec_stats['mean'] / 1000)) / 1024  # KB/s
    
    print(f"\n📈 THROUGHPUT:")
    print(f"   🔐 Encryption: {throughput_enc:.2f} KB/s")
    print(f"   🔓 Decryption: {throughput_dec:.2f} KB/s")
    
    # Total time
    total_enc = sum(enc_times)
    total_dec = sum(dec_times)
    
    print(f"\n⏰ TOTAL TIME ({len(enc_times)} iterations):")
    print(f"   🔐 Encryption: {total_enc:.2f} ms ({total_enc/1000:.4f} s)")
    print(f"   🔓 Decryption: {total_dec:.2f} ms ({total_dec/1000:.4f} s)")
    print(f"   🔄 Total:      {total_enc + total_dec:.2f} ms ({(total_enc+total_dec)/1000:.4f} s)")

def save_results_to_file(all_results):
    """Simpan hasil ke file"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"performance_results_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("="*70 + "\n")
        f.write("ASCON PERFORMANCE TEST RESULTS\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Algorithm: {VARIANT}\n")
        f.write(f"Iterations: {NUM_ITERATIONS}\n")
        f.write("="*70 + "\n\n")
        
        for data_type, results in all_results.items():
            f.write(f"\n{data_type.upper()} DATA\n")
            f.write("-"*70 + "\n")
            f.write(f"Plaintext size: {results['size']} bytes\n")
            f.write(f"\nEncryption:\n")
            f.write(f"  Min:    {results['enc_stats']['min']:.4f} ms\n")
            f.write(f"  Max:    {results['enc_stats']['max']:.4f} ms\n")
            f.write(f"  Mean:   {results['enc_stats']['mean']:.4f} ms\n")
            f.write(f"  Median: {results['enc_stats']['median']:.4f} ms\n")
            f.write(f"  StdDev: {results['enc_stats']['stdev']:.4f} ms\n")
            f.write(f"\nDecryption:\n")
            f.write(f"  Min:    {results['dec_stats']['min']:.4f} ms\n")
            f.write(f"  Max:    {results['dec_stats']['max']:.4f} ms\n")
            f.write(f"  Mean:   {results['dec_stats']['mean']:.4f} ms\n")
            f.write(f"  Median: {results['dec_stats']['median']:.4f} ms\n")
            f.write(f"  StdDev: {results['dec_stats']['stdev']:.4f} ms\n")
            f.write(f"\nThroughput:\n")
            f.write(f"  Encryption: {results['throughput_enc']:.2f} KB/s\n")
            f.write(f"  Decryption: {results['throughput_dec']:.2f} KB/s\n")
            f.write("\n")
    
    print(f"\n💾 Results saved to: {filename}")

# ===== MAIN PROGRAM =====
def main():
    print("="*70)
    print("🚀 ASCON PERFORMANCE TESTING")
    print("="*70)
    print(f"🔐 Algorithm: {VARIANT}")
    print(f"🔢 Iterations per test: {NUM_ITERATIONS}")
    print(f"📦 Test data sizes: {len(test_data)} variations")
    print("="*70)
    
    all_results = {}
    
    for data_type, plaintext in test_data.items():
        print(f"\n\n🔬 Testing {data_type.upper()} data...")
        print(f"📏 Size: {len(plaintext)} bytes")
        
        # Test Encryption
        print("🔐 Testing encryption...")
        enc_times, ciphertext = test_encryption(plaintext, NUM_ITERATIONS)
        enc_stats = calculate_stats(enc_times)
        
        if ciphertext is None:
            print("❌ Encryption failed!")
            continue
        
        # Test Decryption
        print("🔓 Testing decryption...")
        dec_times = test_decryption(ciphertext, NUM_ITERATIONS)
        
        if dec_times is None:
            print("❌ Decryption failed!")
            continue
        
        dec_stats = calculate_stats(dec_times)
        
        # Calculate throughput
        throughput_enc = (len(plaintext) / (enc_stats['mean'] / 1000)) / 1024
        throughput_dec = (len(plaintext) / (dec_stats['mean'] / 1000)) / 1024
        
        # Store results
        all_results[data_type] = {
            'size': len(plaintext),
            'enc_stats': enc_stats,
            'dec_stats': dec_stats,
            'throughput_enc': throughput_enc,
            'throughput_dec': throughput_dec
        }
        
        # Print results
        print_results(data_type, plaintext, enc_stats, dec_stats, enc_times, dec_times)
    
    # Save to file
    save_results_to_file(all_results)
    
    print("\n" + "="*70)
    print("✅ Testing completed!")
    print("="*70)

if __name__ == "__main__":
    main()