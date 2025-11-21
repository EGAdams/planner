#!/usr/bin/env node

/**
 * Test script to upload and scan a receipt image
 * Usage: node test-receipt-scan.js
 */

import fs from 'fs';
import path from 'path';
import { Blob } from 'buffer';

const API_BASE = 'http://localhost:8080/api';
const IMAGE_PATH = 'C:\\Users\\NewUser\\Documents\\meijer_vander_vilet_feb_09.jpeg';

async function testReceiptScan() {
    console.log('🔍 Testing Receipt Scan API');
    console.log('='.repeat(60));
    console.log(`📁 Image file: ${IMAGE_PATH}`);
    console.log('');

    // Check if file exists
    if (!fs.existsSync(IMAGE_PATH)) {
        console.error(`❌ Error: File not found at ${IMAGE_PATH}`);
        process.exit(1);
    }

    const fileStats = fs.statSync(IMAGE_PATH);
    console.log(`✅ File found (${(fileStats.size / 1024).toFixed(2)} KB)`);
    console.log('');

    // Create form data
    const fileBuffer = fs.readFileSync(IMAGE_PATH);
    const blob = new Blob([fileBuffer], { type: 'image/jpeg' });
    const form = new FormData();
    form.append('file', blob, path.basename(IMAGE_PATH));

    console.log('📤 Uploading receipt to API...');
    console.log(`   Endpoint: ${API_BASE}/parse-receipt`);
    console.log('');

    const startTime = Date.now();

    try {
        const response = await fetch(`${API_BASE}/parse-receipt`, {
            method: 'POST',
            body: form
        });

        const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        console.log(`⏱️  Response received in ${elapsed}s`);
        console.log(`   Status: ${response.status} ${response.statusText}`);
        console.log('');

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ API Error:');
            console.error(errorText);
            process.exit(1);
        }

        const result = await response.json();

        console.log('✅ Receipt parsed successfully!');
        console.log('='.repeat(60));
        console.log('');

        // Display parsed data
        console.log('📋 PARSED RECEIPT DATA:');
        console.log('='.repeat(60));

        if (result.parsed_data) {
            const data = result.parsed_data;

            // Merchant info
            console.log('\n🏪 MERCHANT INFORMATION:');
            console.log(`   Name: ${data.party?.merchant_name || 'N/A'}`);
            console.log(`   Date: ${data.transaction_date || 'N/A'}`);
            console.log(`   Payment Method: ${data.payment_method || 'N/A'}`);

            // Totals
            console.log('\n💰 TOTALS:');
            console.log(`   Subtotal: $${data.totals?.subtotal || '0.00'}`);
            console.log(`   Tax: $${data.totals?.tax_amount || '0.00'}`);
            console.log(`   Total: $${data.totals?.total_amount || '0.00'}`);

            // Items
            console.log('\n🛒 ITEMS:');
            if (data.items && data.items.length > 0) {
                console.log(`   Found ${data.items.length} items:\n`);

                let calculatedTotal = 0;
                data.items.forEach((item, index) => {
                    const lineTotal = parseFloat(item.line_total || 0);
                    calculatedTotal += lineTotal;

                    console.log(`   ${index + 1}. ${item.description}`);
                    console.log(`      Qty: ${item.quantity} × $${item.unit_price} = $${item.line_total}`);
                });

                console.log('');
                console.log(`   Calculated Total: $${calculatedTotal.toFixed(2)}`);
                console.log(`   Receipt Total: $${data.totals?.total_amount || '0.00'}`);

                const diff = Math.abs(calculatedTotal - parseFloat(data.totals?.total_amount || 0));
                if (diff < 0.01) {
                    console.log('   ✅ Totals match!');
                } else {
                    console.log(`   ⚠️  Difference: $${diff.toFixed(2)}`);
                }
            } else {
                console.log('   No items found');
            }

            // Metadata
            console.log('\n📝 METADATA:');
            console.log(`   Temp file: ${result.temp_file_name || 'N/A'}`);
            console.log(`   Confidence: ${data.meta?.confidence || 'N/A'}`);
        }

        console.log('');
        console.log('='.repeat(60));
        console.log('');

        // Validation checks
        console.log('🔍 VALIDATION CHECKS:');
        console.log('='.repeat(60));

        const checks = [];

        if (result.parsed_data?.party?.merchant_name) {
            checks.push('✅ Merchant name extracted');
        } else {
            checks.push('❌ Merchant name missing');
        }

        if (result.parsed_data?.transaction_date) {
            checks.push('✅ Transaction date extracted');
        } else {
            checks.push('❌ Transaction date missing');
        }

        if (result.parsed_data?.totals?.total_amount) {
            checks.push('✅ Total amount extracted');
        } else {
            checks.push('❌ Total amount missing');
        }

        if (result.parsed_data?.items && result.parsed_data.items.length > 0) {
            checks.push(`✅ ${result.parsed_data.items.length} items extracted`);
        } else {
            checks.push('❌ No items extracted');
        }

        checks.forEach(check => console.log(`   ${check}`));

        console.log('');
        console.log('='.repeat(60));
        console.log('✅ Test completed successfully!');

    } catch (error) {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        console.error(`\n❌ Error after ${elapsed}s:`);
        console.error(error.message);
        console.error('');
        console.error('Stack trace:');
        console.error(error.stack);
        process.exit(1);
    }
}

// Run the test
testReceiptScan();
