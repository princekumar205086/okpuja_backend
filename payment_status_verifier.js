/**
 * Frontend Payment Status Verification Helper
 * Call this function after user returns from PhonePe payment to verify status
 */

class PaymentStatusVerifier {
    constructor(apiBaseUrl, authToken) {
        this.apiBaseUrl = apiBaseUrl || 'http://localhost:8000';
        this.authToken = authToken;
    }

    /**
     * Verify payment status and trigger booking creation if successful
     * @param {number} paymentId - Payment ID to verify
     * @returns {Promise<Object>} - Verification result
     */
    async verifyPaymentStatus(paymentId) {
        try {
            console.log(`🔍 Verifying payment status for Payment ID: ${paymentId}`);
            
            const response = await fetch(`${this.apiBaseUrl}/api/payments/payments/${paymentId}/verify-status/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                console.log('✅ Payment status verification completed');
                console.log(`Status: ${result.old_status} → ${result.new_status}`);
                
                // Handle different scenarios
                if (result.status_updated && result.new_status === 'SUCCESS') {
                    console.log('🎉 Payment verified as successful!');
                    
                    if (result.booking_created) {
                        console.log(`📅 Booking created: ${result.booking_id}`);
                        return {
                            success: true,
                            paymentSuccessful: true,
                            bookingCreated: true,
                            bookingId: result.booking_id,
                            message: 'Payment successful and booking created!'
                        };
                    } else {
                        return {
                            success: true,
                            paymentSuccessful: true,
                            bookingCreated: false,
                            message: 'Payment successful but booking creation pending'
                        };
                    }
                } else if (result.new_status === 'SUCCESS') {
                    return {
                        success: true,
                        paymentSuccessful: true,
                        bookingCreated: result.booking_created,
                        message: 'Payment was already successful'
                    };
                } else if (result.new_status === 'FAILED') {
                    return {
                        success: true,
                        paymentSuccessful: false,
                        bookingCreated: false,
                        message: 'Payment failed'
                    };
                } else {
                    return {
                        success: true,
                        paymentSuccessful: false,
                        bookingCreated: false,
                        message: 'Payment still pending'
                    };
                }
            } else {
                console.error('❌ Payment status verification failed:', result.error);
                return {
                    success: false,
                    error: result.error,
                    message: 'Failed to verify payment status'
                };
            }

        } catch (error) {
            console.error('❌ Error verifying payment status:', error);
            return {
                success: false,
                error: error.message,
                message: 'Network error during payment verification'
            };
        }
    }

    /**
     * Poll payment status until it's no longer pending
     * @param {number} paymentId - Payment ID to monitor
     * @param {number} maxAttempts - Maximum polling attempts (default: 10)
     * @param {number} intervalMs - Polling interval in milliseconds (default: 3000)
     * @returns {Promise<Object>} - Final verification result
     */
    async pollPaymentStatus(paymentId, maxAttempts = 10, intervalMs = 3000) {
        console.log(`🔄 Starting payment status polling for Payment ID: ${paymentId}`);
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            console.log(`📡 Polling attempt ${attempt}/${maxAttempts}`);
            
            const result = await this.verifyPaymentStatus(paymentId);
            
            if (result.success && result.paymentSuccessful !== undefined) {
                // Payment status is determined (success or failed)
                return result;
            }
            
            if (attempt < maxAttempts) {
                console.log(`⏳ Payment still pending, waiting ${intervalMs/1000}s before next check...`);
                await new Promise(resolve => setTimeout(resolve, intervalMs));
            }
        }
        
        // Max attempts reached
        return {
            success: false,
            error: 'Max polling attempts reached',
            message: 'Payment status could not be determined within time limit'
        };
    }

    /**
     * Check booking status for a payment
     * @param {number} paymentId - Payment ID to check
     * @returns {Promise<Object>} - Booking status result
     */
    async checkBookingStatus(paymentId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/payments/payments/${paymentId}/check-booking/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            return result;

        } catch (error) {
            console.error('❌ Error checking booking status:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

/**
 * Usage example:
 * 
 * // After user returns from PhonePe payment
 * const verifier = new PaymentStatusVerifier('http://localhost:8000', authToken);
 * 
 * // Option 1: Single verification
 * const result = await verifier.verifyPaymentStatus(paymentId);
 * if (result.paymentSuccessful && result.bookingCreated) {
 *     // Redirect to booking confirmation page
 *     window.location.href = `/booking-confirmation/${result.bookingId}`;
 * }
 * 
 * // Option 2: Poll until status is determined
 * const finalResult = await verifier.pollPaymentStatus(paymentId);
 * if (finalResult.paymentSuccessful) {
 *     // Handle successful payment
 * } else {
 *     // Handle failed payment
 * }
 */

// For use in browser
if (typeof window !== 'undefined') {
    window.PaymentStatusVerifier = PaymentStatusVerifier;
}

// For use in Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PaymentStatusVerifier;
}
