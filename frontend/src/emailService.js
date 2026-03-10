import emailjs from 'emailjs-com';

const SERVICE_ID = 'service_q8nz87h';
const PUBLIC_KEY = 'I3ljGz81XKibPuUjm';

export const emailService = {
    sendAlert: async (patientName, alertType, severity, description) => {
        const templateParams = {
            to_name: 'Medical Staff',
            patient_name: patientName,
            alert_type: alertType,
            severity: severity,
            description: description,
            timestamp: new Date().toLocaleString()
        };

        try {
            const response = await emailjs.send(
                SERVICE_ID,
                'template_axf2tp9',
                templateParams,
                PUBLIC_KEY
            );
            console.log('Email sent successfully!', response.status, response.text);
            return response;
        } catch (error) {
            console.error('Failed to send email:', error);
            throw error;
        }
    },

    sendOTP: async (userEmail, otp) => {
        const templateParams = {
            to_email: userEmail,
            otp_code: otp,
            timestamp: new Date().toLocaleString()
        };

        try {
            const response = await emailjs.send(
                SERVICE_ID,
                'template_q5z6vfz',
                templateParams,
                PUBLIC_KEY
            );
            console.log('OTP Email sent successfully!', response.status, response.text);
            return response;
        } catch (error) {
            console.error('Failed to send OTP email:', error);
            throw error;
        }
    }
};
