/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "i2c.h"
#include "spi.h"
#include "tim.h"
#include "usb_device.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "usbd_cdc_if.h"
#include "usbd_core.h" // Include for USB device core structures
#include <math.h>
//#include "EMA.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
// # samples per data block(half buffer)
#define DATASIZE 128
// full buffer size
#define BUFFERSIZE DATASIZE * 2
#define PI 3.14159265358979323846
#define FLOAT_SCALE 2147483648
//BUFFERS
uint16_t adc_vals[BUFFERSIZE]; //adc buffer
uint8_t USB_test_1[BUFFERSIZE];
uint8_t USB_test_2[BUFFERSIZE];
uint8_t USB_test_3[BUFFERSIZE];
uint8_t USB_test_4[BUFFERSIZE];
uint8_t USB_test_5[BUFFERSIZE];
uint8_t USB_test_6[BUFFERSIZE];
uint8_t USB_test_7[BUFFERSIZE];
uint8_t USB_test_8[BUFFERSIZE];
uint8_t* test_buffers[] = {
    USB_test_1,
    USB_test_2,
    USB_test_3,
    USB_test_4,
    USB_test_5,
    USB_test_6,
    USB_test_7,
    USB_test_8
};

uint16_t live_read_packet[54];
uint16_t unpacked_1[BUFFERSIZE];
uint16_t unpacked_2[BUFFERSIZE];
uint16_t unpacked_3[BUFFERSIZE];
uint16_t* unpacked_buffers[] = {
		unpacked_1,
		unpacked_2,
		unpacked_3
};

uint32_t start_time, end_time, elapsed_time;

uint32_t dac_vals[BUFFERSIZE]; //dac buffer (may need to be larger for multiple output signals later
uint8_t data_ready;
int result;
int result_2;
float frequency = 1.0;       // 1 Hz sine wave
float amplitude = 1.0;       // Amplitude of 1
float sample_rate = 100.0;   // 100 samples per second
int package_counter = 0;
int num_full_buffers_packed = 0;

uint8_t entered_transfer = 0;
extern USBD_HandleTypeDef hUsbDeviceFS;
#define CHUNK_SIZE 4

//debug signals
uint16_t check;
uint8_t cnt;
int track;
int button_pressed = 0;

// pointers to the half of the buffer being processed
static volatile uint32_t* input_buffer_ptr;
static volatile uint32_t* output_buffer_ptr = &dac_vals[0];
//EMA filter;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
void set_buffer_terminator(uint8_t* buffer, uint32_t size) {
    if (size >= 2) {  // Ensure there's enough space for \r\n
        buffer[size - 2] = '\r';  // Set second to last byte to '\r'
        buffer[size - 1] = '\n';   // Set last byte to '\n'
    }
}
void fill_test_buffers(void) {
	for (int i = 0; i < BUFFERSIZE; i++) {
	        adc_vals[i] = 2;
	    }
    for (int i = 0; i < BUFFERSIZE; i++) {
        USB_test_1[i] = "Test_1"[i % 6];
    }
    set_buffer_terminator(USB_test_1, BUFFERSIZE);

    for (int i = 0; i < BUFFERSIZE; i++) {
        USB_test_2[i] = "Test_2"[i % 6];
    }
    set_buffer_terminator(USB_test_2, BUFFERSIZE);

    for (int i = 0; i < BUFFERSIZE; i++) {
        USB_test_3[i] = "Test_3"[i % 6];
    }
    set_buffer_terminator(USB_test_3, BUFFERSIZE);

    for (int i = 0; i < BUFFERSIZE; i++) {
        USB_test_4[i] = "Test_4"[i % 6];
    }
    set_buffer_terminator(USB_test_4, BUFFERSIZE);

    for (int i = 0; i < BUFFERSIZE; i++) {
        USB_test_5[i] = "Test_5"[i % 6];
    }
    set_buffer_terminator(USB_test_5, BUFFERSIZE);

    for (int i = 0; i < BUFFERSIZE; i++) {
        USB_test_6[i] = "Test_6"[i % 6];
    }
    set_buffer_terminator(USB_test_6, BUFFERSIZE);

    for (int i = 0; i < BUFFERSIZE; i++) {
        USB_test_7[i] = "Test_7"[i % 6];
    }
    set_buffer_terminator(USB_test_7, BUFFERSIZE);

    for (int i = 0; i < BUFFERSIZE; i++) {
        USB_test_8[i] = "Test_8"[i % 6];
    }
    set_buffer_terminator(USB_test_8, BUFFERSIZE);
}



/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

uint8_t is_usb_connected(void) {
    if (hUsbDeviceFS.dev_state == USBD_STATE_CONFIGURED) {
        return 1; // USB is connected
    } else {
        return 0; // USB is not connected
    }
}

void data_transfer_USB(uint8_t* data, uint16_t size) {
	entered_transfer = 193;
//    result = CDC_Transmit_FS(USB_test, strlen((char*)USB_test));
	result = CDC_Transmit_FS(data, size);

	    // Print the result of the transmission
	    switch (result) {
	        case USBD_OK:
	            printf("USB transmission successful.\n");
	            break;
	        case USBD_BUSY:
	            printf("USB transmission failed: BUSY.\n");
	            break;
	        case USBD_FAIL:
	            printf("USB transmission failed: ERROR.\n");
	            break;
	        default:
	            printf("USB transmission failed: Unknown status.\n");
	            break;
	    }
}

void transfer_all_buffers(void) {
    // Number of buffers
    uint8_t num_buffers = sizeof(test_buffers) / sizeof(test_buffers[0]);
    for (uint8_t i = 0; i < num_buffers; i++) {
        uint16_t size = strlen((char*)test_buffers[i]);
        data_transfer_USB(test_buffers[i], size);
        HAL_Delay(100);
    }
}

void sendBufferOverUSB(uint32_t* buffer, uint32_t size) {
    // Allocate a byte array to hold the uint32_t data
    uint8_t byteBuffer[size * sizeof(uint32_t)];

    // Convert the uint32_t buffer to uint8_t
    for (uint32_t i = 0; i < size; i++) {
        byteBuffer[i * sizeof(uint32_t)]     = (buffer[i] >> 24) & 0xFF; // MSB
        byteBuffer[i * sizeof(uint32_t) + 1] = (buffer[i] >> 16) & 0xFF;
        byteBuffer[i * sizeof(uint32_t) + 2] = (buffer[i] >> 8) & 0xFF;
        byteBuffer[i * sizeof(uint32_t) + 3] = buffer[i] & 0xFF; // LSB
    }

    // Send the byte array using the CDC interface
    CDC_Transmit_FS(byteBuffer, size * sizeof(uint32_t));
}

void send_raw_adc_data(uint32_t* adc_vals, uint32_t num_samples) {
    // Size of the buffer in bytes
    uint32_t size_to_send = num_samples * sizeof(uint32_t);  // num_samples * 4 bytes

    // Transmit the raw data as bytes
    if (CDC_Transmit_FS((uint8_t*)adc_vals, size_to_send) != USBD_OK) {
        // Handle error if needed
    }
}

void generate_sine_wave(float frequency, float amplitude, float sample_rate, uint32_t buffer[], int buffer_size) {
    for (int i = 0; i < buffer_size; i++) {
        // Time variable as a scaled integer to avoid floating-point math
        int64_t t = (int64_t)(i * UINT32_MAX / sample_rate); // Scale time

        // Compute the sine value as a fixed-point representation
        // sin(2 * PI * frequency * t) is scaled up by a factor of 2^30 for better precision
        int32_t sine_value = (int32_t)(amplitude * sin(2 * PI * frequency * ((double)t / UINT32_MAX)) * (1 << 30));

        // Convert sine value to a uint32_t in the range [0, UINT32_MAX]
        // Note: The range of sine_value is [-amplitude, amplitude], so we scale and offset
        buffer[i] = (uint32_t)((sine_value + (int32_t)amplitude * (1 << 30)) / ((int32_t)(2 * amplitude) * (1 << 30)) * UINT32_MAX);
    }
}

void send_sine_wave_data() {
    for (int i = 0; i < BUFFERSIZE; i += CHUNK_SIZE) {
        // Check to ensure we don't exceed the buffer size
        if (i + CHUNK_SIZE <= BUFFERSIZE) {
            uint8_t* byte_buffer = (uint8_t*)&adc_vals[i]; // Cast to uint8_t pointer
            CDC_Transmit_FS(byte_buffer, CHUNK_SIZE * sizeof(uint32_t)); // Send 16 bytes (4 uint32_t)
        }
    }
}
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
	input_buffer_ptr = &adc_vals[DATASIZE];
//	output_buffer_ptr = &dac_vals[DATASIZE];

	check = 1;

	data_ready = 1;
//	CDC_Transmit_FS((uint8_t*)&adc_vals, sizeof(adc_vals));
}
void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef* hadc)
{
	input_buffer_ptr = &adc_vals[0];
//	output_buffer_ptr = &dac_vals[0];

	check = 2;

	data_ready = 1;
//	CDC_Transmit_FS((uint8_t*)input_buffer_ptr, 0.5 * sizeof(adc_vals));
}

void package_point(uint16_t* final_packet_buffer, const uint16_t* unpacked_buffer, uint16_t identifier, int final_packet_pointer, int buffer_pointer, int num_points) {
	uint16_t zero = 0;
	final_packet_buffer[final_packet_pointer * (num_points + 2)] = zero;
	final_packet_buffer[final_packet_pointer * (num_points + 2) + 1] = identifier;
	for (int i = 0; i < num_points; i++) {
		final_packet_buffer[final_packet_pointer * (num_points + 2) + 2 + i] = unpacked_buffer[buffer_pointer + i];
	}
//	final_packet_buffer[final_packet_pointer * 3 + 2] = unpacked_buffer[buffer_pointer];

}

void package_point_per_buffer(uint16_t* final_packet_buffer, uint16_t** unpacked_buffers, int num_unpacked_buffers, int buffer_pointer) {
	for(int i = 0; i < num_unpacked_buffers; i++) {
//		package_point(final_packet_buffer, unpacked_buffers[i], (uint16_t) i + 1, i, buffer_pointer);
//		track++;
	}
}

void package_several_points_per_buffer(uint16_t* final_packet_buffer, uint16_t** unpacked_buffers, int num_unpacked_buffers, int buffer_pointer, int num_points) {
	for(int i = 0; i < num_unpacked_buffers; i++) {
			package_point(final_packet_buffer, unpacked_buffers[i], (uint16_t) i + 1, i, buffer_pointer, num_points);
	//		track++;
		}
}

void fill_unpacked_buffers(uint16_t** unpacked_buffers, int num_unpacked_buffers) {
	for(int i = 0; i < num_unpacked_buffers; i++) {
		for (int j = 0; j < BUFFERSIZE; j++) {
//			unpacked_buffers[i][j] = j * 10 + i;
			unpacked_buffers[i][j] = i * 1000 + 500;
		}
	}
}

void wait_for_button_press(GPIO_TypeDef *GPIOx, uint16_t GPIO_Pin) {
    // Wait until the button is pressed (assuming active-low button, meaning pressed is 0)
	while (HAL_GPIO_ReadPin(GPIOx, GPIO_Pin) == GPIO_PIN_RESET) {
	        // Optionally add a small delay to avoid busy waiting
	        HAL_Delay(50);
	    }
	    // Optionally, wait for the button to be released
	    while (HAL_GPIO_ReadPin(GPIOx, GPIO_Pin) == GPIO_PIN_SET) {
	        HAL_Delay(50);
	    }
	HAL_GPIO_TogglePin(GPIOE, GPIO_PIN_11); // Toggle the green LED
    button_pressed = 1;
}


/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */
  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_I2C1_Init();
  MX_SPI1_Init();
  MX_ADC1_Init();
  MX_TIM6_Init();
  MX_USB_DEVICE_Init();
  /* USER CODE BEGIN 2 */
  // START TIME BASE AND DMA CHANNELS
  HAL_TIM_Base_Start(&htim6);
  HAL_ADC_Start_DMA(&hadc1, (uint16_t *) adc_vals, BUFFERSIZE);
  fill_test_buffers();
  HAL_Delay(5000);


  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */

//  	while (!is_usb_connected()) {
//  		  HAL_Delay(100);
//  	  }
    fill_unpacked_buffers(unpacked_buffers, 3);
//  	package_point_per_buffer(live_read_packet, unpacked_buffers, 3, 0);
  	package_several_points_per_buffer(live_read_packet, unpacked_buffers, 3, package_counter, 16);

//    for(int i = 0; i < BUFFERSIZE; i++) {
//        	adc_vals[i] = 8;
//        }
    wait_for_button_press(GPIOA, GPIO_PIN_0);

  	start_time = HAL_GetTick();
  	HAL_Delay(1);
//  	result = CDC_Transmit_FS((uint8_t*)&live_read_packet, sizeof(live_read_packet));
//  	result_2 = CDC_Transmit_FS((uint8_t*)&adc_vals, sizeof(adc_vals));
//  	transfer_all_buffers();
  	end_time = HAL_GetTick();
  	elapsed_time = end_time - start_time;
  	printf("Elapsed time: %u\n", elapsed_time);
//  	generate_sine_wave(frequency, amplitude, sample_rate, adc_vals, BUFFERSIZE);


  while (1)
  {
	  if(package_counter >= BUFFERSIZE) {
	  		  package_counter = 0;
	  		  num_full_buffers_packed++;
	  }
//	  	for(int i = 0; i < 16; i++) {
//	  		package_point_per_buffer(live_read_packet, unpacked_buffers, 3, package_counter);
//	  		package_counter++;
//	  	}
	  	package_several_points_per_buffer(live_read_packet, unpacked_buffers, 3, package_counter, 16);
	  	package_counter += 16;
	  	result = CDC_Transmit_FS((uint8_t*)&live_read_packet, sizeof(live_read_packet));
	  	HAL_Delay(5);
//	  	package_counter++;

//	  transfer_all_buffers();
//	while (!is_usb_connected()) {
//	      HAL_Delay(100);
//	}
//
//	transfer_all_buffers();
//	  uint8_t four_byte_string[4] = "ABCD";  // 4-byte string
//	  CDC_Transmit_FS((uint8_t*)four_byte_string, 4);  // Sending 4 bytes over USB
//	  uint32_t number = 42;  // Example integer
//	  uint8_t data[4];
//
//	  // Break the 32-bit integer into 4 bytes
//	  data[0] = (number >> 24) & 0xFF;
//	  data[1] = (number >> 16) & 0xFF;
//	  data[2] = (number >> 8) & 0xFF;
//	  data[3] = number & 0xFF;
//
//	  CDC_Transmit_FS(data, 4);  // Send the 4 bytes representing the integer
	  uint32_t value = 1234;  // Example uint32_t value
//	  CDC_Transmit_FS((uint8_t*)&adc_vals, sizeof(adc_vals));
//	  send_sine_wave_data();
//	  result = CDC_Transmit_FS((uint8_t*)&live_read_packet, sizeof(live_read_packet));

	  HAL_Delay(2);
//	sendBufferOverUSB(adc_vals, BUFFERSIZE); // Send the buffer over USB
//	send_raw_adc_data(adc_vals, BUFFERSIZE);

//	HAL_Delay(1000);
  }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI|RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_BYPASS;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_USB|RCC_PERIPHCLK_I2C1
                              |RCC_PERIPHCLK_ADC12;
  PeriphClkInit.Adc12ClockSelection = RCC_ADC12PLLCLK_DIV1;
  PeriphClkInit.I2c1ClockSelection = RCC_I2C1CLKSOURCE_HSI;
  PeriphClkInit.USBClockSelection = RCC_USBCLKSOURCE_PLL_DIV1_5;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
