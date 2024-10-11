/*
 * IIR.c
 *
 *  Created on: Sep 24, 2024
 *      Author: akarl
 */

#include "IIR.h"

void IIR1_Init(IIR1 *filt, float a1, float b1, float b2){
	filt->a = a1;

	filt->b[0] = b1;
	filt->b[1] = b2;

	filt->x[0] = 0;
	filt->x[1] = 0;

	filt->y = 0;

	filt->out = 0.0;
}

float IIR1_Update(IIR1 *filt, float input){
	filt->x[0] = input;

	filt->y = filt->out;

	filt->out = (filt->b[0] * filt->x[0]) +
				(filt->b[1] * filt->x[1]) -
				(filt->a * filt->y);

	filt->x[1] = filt->x[0];

	return filt->out;

}

void IIR2_Init(IIR2 *filt, float a1,  float a2,  float b1, float b2, float b3){
	filt->a[0] = a1;
	filt->a[1] = a2;

	filt->b[0] = b1;
	filt->b[1] = b2;
	filt->b[2] = b3;

	filt->x[0] = 0;
	filt->x[1] = 0;
	filt->x[2] = 0;

	filt->y[0] = 0;
	filt->y[1] = 0;

	filt->out = 0.0;
}

float IIR2_Update(IIR2 *filt, float input){
	filt->x[0] = input;

	filt->y[1] = filt->y[0];
	filt->y[0] = filt->out;

	filt->out = (filt->b[0] * filt->x[0]) +
				(filt->b[1] * filt->x[1]) +
				(filt->b[2] * filt->x[2]) -
				(filt->a[0] * filt->y[0]) -
				(filt->a[1] * filt->y[1]);

//	output[n] = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;

	filt->x[2] = filt->x[1];
	filt->x[1] = filt->x[0];

	return filt->out;

}

void IIR3_Init(IIR3 *filt, float a1,  float a2, float a3, float b1, float b2, float b3, float b4){
	filt->a[0] = a1;
	filt->a[1] = a2;
	filt->a[2] = a3;

	filt->b[0] = b1;
	filt->b[1] = b2;
	filt->b[2] = b3;
	filt->b[3] = b4;

	filt->x[0] = 0;
	filt->x[1] = 0;
	filt->x[2] = 0;
	filt->x[3] = 0;

	filt->y[0] = 0;
	filt->y[1] = 0;
	filt->y[2] = 0;

	filt->out = 0.0;
}

float IIR3_Update(IIR3 *filt, float input) {
    // Store the current input
    filt->x[0] = input;

    // Apply the IIR filter equation (third-order)
    filt->out = (filt->b[0] * filt->x[0]) +
                (filt->b[1] * filt->x[1]) +
                (filt->b[2] * filt->x[2]) +
                (filt->b[3] * filt->x[3]) -
                (filt->a[0] * filt->y[0]) -  // Corresponds to y[n-1]
                (filt->a[1] * filt->y[1]) -  // Corresponds to y[n-2]
                (filt->a[2] * filt->y[2]);   // Corresponds to y[n-3]

    // Shift the previous input/output values for the next iteration
    filt->x[3] = filt->x[2];
    filt->x[2] = filt->x[1];
    filt->x[1] = filt->x[0];

    filt->y[2] = filt->y[1];
    filt->y[1] = filt->y[0];
    filt->y[0] = filt->out;

    // Return the current filter output
    return filt->out;
}

void IIR4_Init(IIR4 *filt, double a1,  double a2, double a3, double a4, double b1, double b2, double b3, double b4, double b5){
	filt->a[0] = a1;
	filt->a[1] = a2;
	filt->a[2] = a3;
	filt->a[3] = a4;

	filt->b[0] = b1;
	filt->b[1] = b2;
	filt->b[2] = b3;
	filt->b[3] = b4;
	filt->b[4] = b5;

	filt->x[0] = 0;
	filt->x[1] = 0;
	filt->x[2] = 0;
	filt->x[3] = 0;
	filt->x[4] = 0;

	filt->y[0] = 0;
	filt->y[1] = 0;
	filt->y[2] = 0;
	filt->y[3] = 0;

	filt->out = 0.0;
}

double IIR4_Update(IIR4 *filt, double input) {
    // Store the current input
    filt->x[0] = input;
    // Shift the previous input/output values for the next iteration
    filt->x[4] = filt->x[3];
    filt->x[3] = filt->x[2];
    filt->x[2] = filt->x[1];
    filt->x[1] = filt->x[0];

    filt->y[3] = filt->y[2];
	filt->y[2] = filt->y[1];
	filt->y[1] = filt->y[0];
	filt->y[0] = filt->out;
    // Apply the IIR filter equation (fourth-order)
    filt->out = (filt->b[0] * filt->x[0]) +
                (filt->b[1] * filt->x[1]) +
                (filt->b[2] * filt->x[2]) +
                (filt->b[3] * filt->x[3]) +
                (filt->b[4] * filt->x[4]) -
                (filt->a[0] * filt->y[0]) -  // Corresponds to y[n-1]
                (filt->a[1] * filt->y[1]) -  // Corresponds to y[n-2]
                (filt->a[2] * filt->y[2]) -  // Corresponds to y[n-3]
                (filt->a[3] * filt->y[3]);   // Corresponds to y[n-4]


    // Return the current filter output
    return filt->out;
}


